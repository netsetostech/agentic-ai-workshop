# Lesson 0.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_0.4_Prove_Switch_Off_WIX.html`, reviewed at blob `227e9752d5a191e48fe77a44ab7d3f59135b88bd`. Learners read that page on the course site; this guide keeps its prose.

Your lane has been up since lesson 0.3. This lesson proves it works from the outside, the way a caller meets it: the kit's preflight, its smoke test, and the three URLs the API answers without a question. Then you break the smoke once, on purpose, and follow the failure to the line of code that printed it and the line that refused. You save the session so the next one starts with one command, switch the lane off, and prove it is off from the instance count Google keeps.

The last part answers the question every learner asks a week later: what does a lane cost when nobody is using it? Zero instances turns out not to be zero cost, and the kit's own teardown has a limit you should know before you rely on it.

- What proving, switching off and tearing down mean

- The words: preflight, smoke, roster, floor, standing cost, state, session keys

- Before you run anything: set up the shell

- The UI: the smoke's question, asked by you

- make preflight: what the lane stands on

- make smoke: one line per check

- Break it once: a tenant nobody lists

- REST: /health, /ready and /version by hand

- Save the session: the state, the inputs, the keys

- make off, and zero instances

- What still bills when nothing runs

- Next session: a restored shell

- make down, and what only deleting the project removes

- Verify it yourself: the checklist

You will learn what proves a deployed lane, how to read a smoke failure down to its cause, what a session saves, and why a lane at zero instances still bills by the hour. Then you will prove it on your lane: preflight clean, smoke green, one 403 read and repaired, zero instances after `make off`, and a restored session that finds the same project and region.

### What proving, switching off and tearing down mean

Three commands that answer three questions, and the one question none of them answers.

Proving a lane means asking it to do its real job end to end, from outside, as a caller would, and reading every answer. A deploy that finished proves only that Google accepted the configuration. It does not prove that the API can reach its index, that the roster lets the right identity in, or that a stranger is kept out. DocuMind's proof is two commands. `make preflight` checks everything the lane stands on (the tools, your sign-in, the project, billing, the state bucket, the APIs) and creates nothing. `make smoke` asks the deployed API a question the golden set says the corpus answers, insists on a cited answer, and then asks again with no token, which must be refused.

Breaking it once is the quickest way to learn to read a failure. You will run the smoke without a tenant, which the Makefile's own header example leaves out, and watch exactly one check fail with the API's own reason. A failure you caused on purpose is one you can read calmly, line by line, back to the code. The next failure will not be on purpose, and you will already know where to look.

Switching off is not tearing down. `make off` lowers four floors to zero: the minimum number of instances Cloud Run keeps warm for the UI, the gateway and the two GPU services. Cloud Run then lets every idle service whose floor is zero fall to zero instances, which on your lane is all of them, and a service at zero instances bills nothing. But six things on the lane are provisioned capacity, not instances, and they bill by the hour whether or not anyone asks a question: the deployed Vector Search index, Spanner's processing units, the GKE cluster and its node, two Cloud SQL databases, and the VPC connector's two machines. Zero instances is not zero cost.

Tearing down is `make down`. It deletes the services, the candidate tag, the context caches and the RAG Engine corpora, then asks Terraform to destroy everything Terraform made. In the one shape the lane runs today, Terraform refuses: two Vertex AI Search data stores carry `prevent_destroy`, and Terraform rejects a whole plan that would destroy one. So `make down` ends by naming what it could not remove, and by printing its last line: delete the project. Shutting a project down is what stops all of its billing.

Saving progress between sessions is three things, none of them a secret: the Terraform state in your state bucket, the inputs `commands/infrastructure.py` confirmed before planning, and the shell variables `commands/session-restart.sh` saves in `~/rag-resume.env`. Next session, one function, `rag_resume`, puts the shell back and proves the API answers.

A hotel room in Pune, booked for the month. Before the guest arrives, housekeeping walks through it: the lights come on, the tap runs, the shower is hot, and the door stays shut to anyone without a key card. When the guest goes out for the day, they switch off the lights and the air conditioner, and the electricity meter stops. The room tariff does not: it is charged every night the room is booked, whether or not anyone sleeps in it. Checking out returns the room, though the cloakroom keeps the bags left there. And if a bag is tagged "do not discard", the desk will not complete the check-out at all; the only way to stop the tariff then is to leave the hotel.

The walk-through is `make smoke`, and the door that stays shut is its last check, the question asked with no token. Switching off the lights is `make off`, and the electricity meter is Cloud Run's instance count. The room tariff is the six provisioned lines. Checking out is `make down`, the cloakroom is Firestore and the buckets that hold files, the tagged bag is the data stores' `prevent_destroy`, and leaving the hotel is deleting the project.

#### The lane's four states, priced

The panel is the lane as the kit defines it. Pick a state and read each row: something the lane runs, bills by the hour, or keeps. The six hourly lines are priced at Google's list prices for Mumbai (asia-south1), where your lane runs, read on 7 October 2026, at Rs 85 to the dollar; step 10 shows every number's source. Your own bill is the number that counts.

Up and Off cost the same by the hour: `make off` lowers floors and removes the vLLM workload from the GKE cluster, and none of the six lines is a floor or that workload: the cluster and its node stay. Down costs the same again today: `make down` deletes the services and the corpora, then Terraform refuses to destroy anything while the two data stores carry `prevent_destroy` (step 12). Only Deleted stops the hourly lines. Five days is the gap between two weekend sessions.

Two things in the panel are worth saying out loud. First, nothing you do inside the lane changes the hourly total: the corpus, the number of questions, the tenants. It is set by what Terraform declared. Second, the biggest line by far is the Vector Search index: with the shard size the kit's comment records, it is Rs 1,839 of the day, 69 percent of it. Step 10 reads the size on your lane.

### The words: preflight, smoke, roster, floor, standing cost, state, session keys

Eleven terms, each with the value it takes on your lane.

Three of these words come in pairs that are easy to confuse, and the lesson keeps them apart. A floor is a setting and an instance count is a measurement: step 9 lowers the first and reads the second. The standing cost is what the lane bills idle, and it has nothing to do with floors: step 10 prices it. And a saved session holds names and values, never credentials: step 11 mints fresh tokens on the way back.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until step 9, just before `make off`.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

### The UI: the smoke's question, asked by you

Before any command, use the lane the way a person does, and notice which identity is asking.

The smoke test in step 5 asks one question. Ask it yourself first, in the browser, so that you know what a working answer looks like before a script judges one. The UI's address is built from your project number and region, the same way the setup block built `API`:

Open it in a browser signed in to Google as the account you gave `make up` as `ADMIN_EMAILS`. Identity-Aware Proxy asks you to sign in, then the Streamlit UI loads. The sidebar shows your email, and on the Chat page, the tenant your email belongs to:

`tenant_for()` is a reverse lookup: it searches every roster for your email and returns the first tenant it finds. `make roster` put your email on acme's roster in lesson 0.3, so the sidebar reads Tenant: acme. Nothing in the browser ever sends a tenant; your email decides it.

Now type the smoke's question into Ask DocuMind...:

After how many years of continuous service does gratuity become payable?

It is golden row lk-16 of `evals/golden.jsonl`, and that row says what a right answer holds: it must contain five years, and the evidence must come from `payment_of_gratuity_act_1972`, the Payment of Gratuity Act, 1972, which sits in all three tenants' corpora. Check both: the phrase in the answer, and the Act among the sources under it. The sidebar's Cost this session panel prices the turn in dollars and rupees, from the tokens the API reports.

Two things happened that the page does not show. If the first load took several seconds, that was a cold start: `documind-ui` had no instance running, because its floor is 0, and your request started one. Step 9 measures the opposite moment, the last instance going away. And your question went to the API as you: the UI forwards the IAP assertion that names your email, and the API checks your email against acme's roster.

The shell is a different caller. The setup block's `tok` function mints a token for `documind-ui-sa`, the UI's own service account, which `make roster` put on all three golden rosters. That is why a shell call may name any of the three tenants, and it is also why the shell must name one: the account belongs to three, and nothing guesses which. Step 6 shows what happens when the smoke names none.

### make preflight: what the lane stands on

11 checks, read-only, each one naming its own fix.

`make preflight` is one line of the Makefile: it hands four variables to a shell script and runs it.

The script is short enough to read whole. It checks the tools (`gcloud`, `terraform`, `make`, `python`), that Terraform is at least 1.9, that gcloud is signed in, that the project exists and has billing, that the state bucket exists, that 22 APIs are enabled, and that the one Python package `make roster` needs is importable. Every check is a read, and every `MISS` line carries the command that fixes it.

Run it with your state bucket. The script's own usage line names the bucket after the project, `-tfstate`, and the cell uses that name unless you have already exported another. Do not leave `TFSTATE_BUCKET` off: the Makefile's default, `documind-tfstate`, is a bucket name only one project in the world can own, and it is not yours.

Read it as a checklist. Every line should say `ok`, and the summary should say `preflight clean`. The advice after it, next: make plan, then make up, is the script speaking to a project that has no lane yet; yours has one, so read the line as "nothing the lane stands on has moved". That is what preflight is for on a running lane: a billing account unlinked, an API disabled, an expired sign-in or an old Terraform in a new shell shows up here, as one `MISS` with its fix, before a `make` target stops halfway. The last line names the one thing no command can check from the shell: the OAuth consent screen that IAP needs.

### make smoke: one line per check

A cited answer, the index that found it, and a refusal, read from the script that asserts them.

`make smoke` is the shortest target in the Makefile, and its header advertises it with one variable:

No `guard-project`, and no variables passed: `smoke.py` reads everything from its environment. These are the names it reads, and what it does when one is missing:

Three of them decide who is asking and about what. `DOCUMIND_PROJECT` gives the identity: without `DOCUMIND_IMPERSONATE_SA`, the script impersonates `documind-ui-sa` in that project. `DOCUMIND_TENANT` gives the tenant, and its default is `tenant-smoke`. Hold on to that default; step 6 is about it. Run the script with no URL at all and it refuses, then prints its own checklist. This costs nothing and touches nothing: `main()` returns before it mints a token or opens a connection.

Lesson numbers in the kit's comments. The kit's comments name lessons by the numbers of the course it was first written for: "12.8", "8.5's gate", "4.6's cell 5", "Module 11's three". The workshop's numbers are the manifest's, and `deploy/INDEX.md` maps every kit file to the lessons on this site that show it. Read a number inside an excerpt as a pointer to history, not to a page here.

Now the checks themselves, in the order they run. The first two need nothing but a token: `/health` must answer 200 with `"ok"`, and `/ready` must answer 200, a 404 being tolerated for a service that has no such route.

The third is the one that proves retrieval. Its comment tells a story worth remembering: the first version asked a question the corpus could not answer, the API refused it correctly, and the test counted the refusal as a pass. Now the question is golden row lk-16, and the check passes only when the answer is `answerable` and carries citations.

The vector-tier check asserts only when the request ran on the kit's own index, which is why the setup section pinned acme there. With the pin, `stages.retrieval_backend` says `vector`, and the check demands that at least one chunk of the pool came from the index rather than from the Firestore rung beneath it.

The last required check asks the same question with no token at all. A service that answers everybody would pass every check above it, so this one asserts a refusal: 401 or 403, and anything else is a failure.

Run it with the three variables, the tenant included. `API`, `PROJECT` and `TENANT` come from the setup block; `TENANT` is acme.

Read it top to bottom. Each `[PASS]` line is one check, with the evidence beside it: the bodies of `/health` and `/ready`, the start of the cited answer, how many chunks the index supplied, and the status the anonymous call received. A `[ -- ]` line is a check that did not apply and says why: the semantic cache is off on the lane, so there is nothing to assert. The `[info]` lines are BigQuery counts the script prints and never asserts. The summary counts passes and failures, and the script exits 0 only with no failure, so `make` reports nothing after it.

### Break it once: a tenant nobody lists

The same smoke without `DOCUMIND_TENANT`: one check fails, and you follow it to the code that printed it and the code that refused.

Run the smoke again without the tenant, which the Makefile's header example leaves out too. Keep the URL and the project, so the smoke still has an identity to ask with. `env -u` makes sure no `DOCUMIND_TENANT` survives from an earlier shell, and the last command prints `make`'s own exit status.

Read the failure in order. The health and readiness lines still pass, so the token got through Cloud Run's door and the service is up. The query line fails, and it says two things: the status, 403, and the body, the API's own words, `not a member of this tenant`. The vector-tier line is simply absent, because there was no answer to inspect. The anonymous call is still refused, so the door is still shut to strangers. The summary counts one failure; `smoke.py` exits 1, and `make` reports `Error 1` on the recipe line and exits 2 itself. One failure, and everything around it working, is the shape of a configuration mistake, not an outage.

Find the line that printed it. It is the last branch of check 3 in step 5: any status other than 200 becomes `bad("query", f"status={st} body={body[:120]}")`. So the body is the API's response, cut at 120 characters, and the words in it came from the API.

Find the line that refused. The API's handler for a question does one thing before anything else: it checks the roster.

A 403 with these words means the API knows exactly who is asking (the token verified) and that this identity is not on the roster of the tenant the question names. It is not the door, which refuses before the API runs, and it is not the token, which the API refuses with a 401 because it does not know who is asking.

Find why. The question named a tenant because `smoke.py` always sends one: `DOCUMIND_TENANT`, and without it, `tenant-smoke`. Its own docstring predicted this failure:

Check the roster. Which tenants is `documind-ui-sa` on? `make roster` decides, through one function in `commands/lane.py`, and its dry run prints the plan without touching Firestore:

The UI's account is on acme, zeta and globex, and no line names `tenant-smoke`. The plan is what `make roster` wrote in lesson 0.3. To see the rosters as they are now, read them from Firestore with the kit's own module:

`tenant-smoke` has no members; acme lists the service accounts and your email. The repair is the variable, not the roster: run step 5's command again, with `DOCUMIND_TENANT="$TENANT"`, and its `[PASS]` lines come back. Putting `documind-ui-sa` on a roster called `tenant-smoke` would not repair it. The roster check would pass, and check 3 would fail one step later as refused or uncited, because that tenant has no documents to answer from: a refused caller turned into a refused answer.

No token, or an account not allowed to invoke the service: Cloud Run's own 403, before the API runs; the anonymous check in step 5 and the last line of step 7 show it. A token that cannot be accepted (the wrong audience, expired, no email in it): a 401, from Cloud Run's door or from the API's `verify_iap`, because nobody can say who is asking. A verified caller on the wrong roster: the 403 above, with the API's words, `not a member of this tenant`. Read the status and the body together and you know which of the three you are looking at before you open a single log.

### REST: /health, /ready and /version by hand

The three GETs the smoke and the restore both use, and what each one can and cannot prove.

Call them yourself, with the setup block's token, then call `/health` once more with no token at all:

Here is what answers. `/health` is one line, and `/version` returns the configuration the revision was deployed with:

`/ready` does more work: it builds the Gemini client and the Firestore client, and on a deployment whose default backend is `vector` it reaches the Vector Search endpoint. A `/health` of 200 beside a failing `/ready` is a service that runs but cannot reach what it reads from.

None of the three takes the caller's identity: no `verify_iap`, no tenant. The token gets you through Cloud Run's door, and that is all they need, which is why `rag_resume` can use them in step 11 to prove a restored shell reaches the API. The fourth line shows the door itself: with no token, Cloud Run refuses before the API runs. Read `/version` field by field once, because it is the first thing to check when an answer changes and nobody deployed: the generator model, the prompt and its version, the retrieval mode and default backend, the graph switch, the embedding the query vectors come from, the ledger's pre-filter, the semantic cache, and the commit the image was built from.

### Save the session: the state, the inputs, the keys

Three things carry a lane from one session to the next, each in its own place, none of them a secret.

"Saving progress" in the kit is not one file. Terraform's record of what exists lives in your state bucket, the values the planner confirmed live beside the Terraform, and your shell's settings live in your home directory. Read the first two directly, then save the third.

#### The Terraform state, in your bucket

`make plan` and `make up` read and write the state through the backend lesson 0.3 initialised: the bucket `TFSTATE_BUCKET` names, under the prefix `TFSTATE_PREFIX`, `documind/` by default. Nothing about the lane's resources is kept on your machine. A fresh clone or a new workstation has no `.terraform/` folder, and `make tf-backend` connects it to the state, but only when the state object exists: it never creates an empty backend in its place.

#### The saved inputs, beside the Terraform

`infrastructure.py` writes the six values it confirmed (`project_id`, `region`, `billing_account_id`, `github_repository`, `github_repository_id`, `deploy_ref`) to the inputs file, and every later plan, check and apply reads them back. A different project or region in the same checkout is refused, never migrated. The selected-plan record is the other file, and it does not outlive the apply:

So after `make up` there is no saved plan waiting to be applied again; the next change to the lane starts with a new `make plan`, which is the point. Read both:

One state object, and the inputs file's names without their values. If the second line says the file does not exist, the inputs live on the machine that ran `make plan`, and that is where the next `make plan` must run.

#### The session keys, in your home directory

`commands/session-restart.sh` is a file you source: it defines functions and runs nothing. These are the names its save function knows:

48 names, the project and the region first. The save writes only the ones your shell has set, and none is a secret: identity tokens are never saved, because the resume mints new ones. Here is the function:

It refuses to save without `PROJECT`, `REGION` and `DEMO_ROOT`, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again:

If `~/rag-source-session.env` does not exist, the save stops with `STOP: Missing rag-source-session.env; restore the original source setup.` The kit's `commands/git-source.sh` writes that file for a source repository that keeps the kit under `deploy/`; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

Then save. The cell exports the two names the helper saves that the setup block calls something else: `PROJECT_NUMBER` (the setup's `NUMBER`) and `OPERATOR_EMAIL` (its `ME`). `TFSTATE_BUCKET` is already exported, from step 4.

The `PASS` line names the file, the names under it are the keys it wrote, and the mode is 600, readable by you alone. Save at the end of every session, after the last change to your shell: a saved session is only as current as the shell it came from.

### make off, and zero instances

Four floors lowered, three of them not yet deployed, then the count that proves the lane is quiet.

First put acme's pin back: run the setup section's second window, the one labelled for the end of the lesson. Then switch off. This is the whole target:

Four switches and a check. Each switch is a make target of its own, and each line starts with `-`, which tells `make` to carry on when the line fails. That matters on your lane. `make up` deploys seven services, and of the four `make off` floors, only `documind-ui` is among them: the small model, the vLLM engine and the gateway arrive in Module 9. Their switches fail on a service that does not exist, `make` notes each error as ignored, and the loop prints `absent` for them. `gke-down` removes the vLLM workload from the GKE cluster, which has none yet, and leaves the cluster and its node standing, as its own message says. The loop at the end reads each floor back from the service's template.

The same four floors are lowered every night at 23:00 IST by the `documind-off` job, so a floor you forget costs an evening; `make off-now` runs that job by hand. Now run the target:

`documind-ui: min-instances 0` is the one floor the lane has; the other three say `absent`. A floor of 0 is a promise about the future, not a count: Cloud Run may keep an idle instance up to 15 minutes after its last request, 10 for a GPU. The proof is the count Google keeps, the same gauge the kit's GPU alarm reads:

One thing `make off` does not cover is worth knowing before you ever raise a floor:

`MIN_INSTANCES` reaches three deploy scripts, the UI's, the MCP server's and the A2A peer's, and `make off` floors only the UI. Deploy with `MIN_INSTANCES=1` for a session day, and the read below will show `documind-mcp` and `documind-agent` still holding an instance after `make off`. The cell waits out the idle window, then reads `instance_count` for every Cloud Run service in the project, one point a minute over the last half hour:

`none - zero instances`: no Cloud Run service is answering, and none is billing. Make no request to the lane between `make off` and the read: the UI, a curl, even the resume's checks in step 11 start an instance and restart the clock. Zero instances is everything `make off` can do. It is not the end of the bill.

### What still bills when nothing runs

Six lines Terraform declared, each billed by the hour, read from the declarations and priced.

With every service at zero, six things on the lane still bill by the hour. None of them is an instance Cloud Run can scale away; each is capacity Terraform provisioned, and each declaration says what it costs or where to look.

#### The six lines, as Terraform declares them

The deployed Vector Search index. An index and an endpoint are records; the deployed index is a machine, and it bills while it serves:

Which machine depends on the index's shard size, which `vector.tf` does not set. The API picks it when the index is created, the map below translates it, and the comment records what the API picked for the index the kit was written against: MEDIUM, served on `e2-standard-16`.

Spanner, provisioned, Enterprise edition, 100 processing units, by the hour:

Cloud SQL: two instances of the cheapest tier, one for the chat service's checkpoints in `cloudsql.tf`, one for the gateway's spend logs in `gateway.tf`, both declared by `make up` whether or not the gateway is ever deployed. The kit's comment gives the tier a rough monthly price; the arithmetic below prices each instance's hours and its disk at the list price instead:

GKE: a regional cluster with one Standard node. Every cluster pays a management fee by the hour; GKE's free-tier credit covers one zonal or Autopilot cluster, and this one is regional, so the fee is paid:

The VPC connector the services reach the network through, whose machines never drop below two:

Two of these comments promise that `make down` removes the resource, and `gke-down`'s message in step 9 says the same of the cluster. Terraform's destroy would remove them all. Step 12 shows why, in the shape the lane runs today, that destroy never starts.

#### The arithmetic

Every unit price is Google's list price for Mumbai (asia-south1), where your lane runs, read on 7 October 2026 on the official pages for Vector Search, Spanner, Cloud SQL, GKE, Compute Engine's E2 machines and its disks. The GKE fee, $0.10 an hour, is the one `gke/README.md` states, and GKE's page says where the free-tier credit applies. The connector guide names `e2-micro` as the machine a connector gets when none is set, and VPC pricing bills connector instances as Compute Engine VMs. A month is 730 hours, 8,760 hours a year over twelve months, and a dollar is Rs 85, the course's rate in `shared/prices.py`.

Rs 2,666 a day, every day the lane exists, whether it is up, off, or still standing after a refused `make down`: Rs 13,332 over the five weekdays between two weekend sessions, Rs 81,100 over a month. It is the figure lesson 0.1 had you write down for a MEDIUM index. The Vector Search node alone is Rs 1,839 a day. The kit's default budget, a `BUDGET_AMOUNT` of 5,000 in the billing account's currency (rupees, on an Indian account), lasts 1.9 days at this rate without a single question asked, and the budget's alerts (`terraform/budget.tf`, lesson 0.1) fire on the way.

With a SMALL index the same day is Rs 1,057. The size is fixed when the index is created, and changing it replaces the index, as the comment in `vector.tf` warns: it is a decision for before `make up`, not after.

The table prices the lane where it runs. Its services, index, databases and cluster are in Mumbai, `asia-south1` (Spanner's configuration is `regional-asia-south1` on every lane), and each unit price is Mumbai's list price as Google's pages gave it on 7 October 2026, before tax. Prices change, and an Indian billing account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. The number that counts is your bill: in the console, Billing, then Reports, filtered to your project and grouped by SKU, on a day the lane sat idle.

What the table leaves out bills by size or by use rather than by the hour: Firestore, the buckets, the container images, the two RAG Engine corpora and the two data stores, the nightly job's minute, the BigQuery tables' few rows. At the corpus's size these are small next to the six lines, and the bill shows them as well. Now read the six lines on your own lane: the machine behind the deployed index and the shard size the API picked, Spanner's edition and units, the databases' tier, the cluster's location and node, the connector's machines.

If your index says `SHARD_SIZE_SMALL` on `e2-standard-2`, use the SMALL figures: the panel in step 1 switches between them. Everything else in the listing should match the table line for line.

### Next session: a restored shell

A new shell, one function, and proof that it found the same project and region, and an API that answers.

Next weekend, the shell you saved from is gone. Open a new one and restore it:

`rag_resume` refuses to start without the saved file, checks the source snapshot again, clears every session name, and sources the file:

Between these lines and the last ones, it activates `rag-shell-venv` and checks that every package the operator commands pin is installed, warns if Terraform is missing, sources the git helper, moves into `DEMO_ROOT`, and refreshes both sign-ins, gcloud's and Python's Application Default Credentials. Then:

`rag_restore_api_url` takes the API's URL from the revision that serves all of the traffic, its `SELF_URL`, not from a guess. `rag_check_resumed_api` mints fresh tokens and calls the three GETs of step 7:

The proof is in the last lines: the project and region the shell found are the ones you saved, the API URL is the serving revision's, and the three GETs answered. From here, copy `API_URL` into `API` and run the setup block's function lines, as the setup section says, and the session carries on where the last one stopped. If the resume stops, its `STOP` line names the fix. Missing packages: run `rag_install_python_dependencies`, a function in the same file, which installs the four requirement files the check reads plus `numpy` and `rank-bm25`, then checks again. A Python sign-in failure: `gcloud auth application-default login`, then the resume again. No saved operator session: step 8's save never ran.

### make down, and what only deleting the project removes

The kit's teardown, the guard that stops its destroy, and the one command that ends the bill.

Module 1 begins on this lane, so do not run `make down` at the end of this lesson. Read what it does now, and run it when you are done with the lane.

In order: `down-services`, then `managed-stores-down`, then `terraform destroy` with the same variables `make plan` used, then the list, whatever the destroy did. `down-services` deletes what Terraform never owned: every service in `DOWN_SERVICES`, the gateway and the two GPU services from Module 9 (the comment's "Module 11's three"), the candidate tag and the tenants' context caches, each on its own line so that an absent one never stops the next:

`managed-stores-down` deletes the RAG Engine corpora for acme and zeta and clears their pins. Then `terraform destroy` plans the destruction of everything in the state, and stops at plan time:

`MANAGED_SEARCH` is true by default, so the state holds two Vertex AI Search data stores, one for acme and one for zeta, each with `prevent_destroy`. Terraform rejects any plan that would destroy such a resource, and a destroy plan destroys everything, so this one destroys nothing: the six lines of step 10 keep billing after `make down`, still Rs 2,666 a day with a MEDIUM index. The list the recipe prints afterwards does not name the data stores; the kit's README does. Lesson 7.3 meets the same guard from the stores' side.

The recipe's last line is the one that ends the bill: delete the throwaway project. Shutting a project down stops all of its billing; for 30 days the project can still be restored, and then it and everything in it are deleted. The same page adds two cautions: charges already run up can still arrive until the current billing cycle ends, and it advises disabling billing on the project before you shut it down. One switch would block the deletion itself: `AUDIT_LOCK=true` locks the audit bucket's five-year retention and liens the project, which is why it is false for a lab.

Read it against the recipe: the deleted and absent lines from `down-services`, the corpora and pins from `managed-stores-down`, Terraform's refusal naming the two data stores, the kit's list, and a non-zero exit, because the recipe exits with the destroy's status. Then, when the course is over, `gcloud projects delete "$PROJECT"` ends every line on this page.

### Verify it yourself: the checklist

Thirteen checks, each one step above, each with what a pass looks like on your lane.

Nothing new bills. `documind-ui`'s floor is 0, now set by `make off` itself; acme's retrieval pin is back on RAG Engine; `~/rag-resume.env` holds your session's names, beside `~/rag-source-session.env` and `~/rag-git-source.sh` if step 8 asked you to write them; the smoke and the UI cost a few questions' tokens. The lane is still up, at zero instances, and still bills the six lines of step 10 for every hour it exists. Module 1 starts on it: lesson 1.1 reads the contracts every source, tenant, page and chunk on this lane obeys.

Netsetos GenAI on GCP · Module 0 Setup · Lesson 0.4 Prove the lane, break it once, and switch it off · v5.0

Next: Module 1 RAG foundation, Lesson 1.1 Understand source, tenant, page and chunk contracts.
