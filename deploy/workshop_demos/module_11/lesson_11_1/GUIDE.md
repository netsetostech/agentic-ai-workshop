# Lesson 11.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.1_Keyless_Deploy_WIX.html`, reviewed at blob `b6503d98ae36784f66986f9b9ccf0d61b9e9b167`. Learners read that page on the course site; this guide keeps its prose.

At lesson 0.3's step 3 your lane was told to trust one GitHub repository, on one branch. This lesson uses that trust. A run of `documind-cd.yml` on your fork asks GitHub for a signed token that names the repository, its id and the branch. Google checks those three against `terraform/wif.tf` and lets the run become `sa-documind-cicd` for about an hour: long enough to build the API's image and put it on a revision that takes no traffic. No key is made, stored or copied anywhere, so there is none to leak. You will set the workflow's four variables from your lane with `make ci-vars`, put a person in front of production, dispatch from `main` and watch it build and deploy, dispatch from a branch and watch it refused, then read the trust, the audit trail and the key count back from Google.

- A pass at the gate, not a key in a drawer

- The words: federation, OIDC token, claim, pool, provider, mapping, condition, STS, binding, impersonation, key, variable, environment, ref

- Before you run anything: set up the shell

- Your fork and your project, as GitHub and the console show them

- What makes it keyless: the trust, the account and the workflow

- Four variables from your lane, and a person in front of production

- A build and a deploy from main, with no key

- A branch dispatch, refused at the auth step

- What Google holds, and who did what

- What may stop the first dispatch, the trust that cannot move, and the path without GitHub

- Verify it yourself: the checklist

You will learn how a GitHub run gets a Google credential without any key, and what stops every other run from getting one. Then you will prove it on your lane: an image built and a candidate revision deployed from your fork's `main`, a branch dispatch refused at the auth step, and zero user-managed keys on every account in the project.

### A pass at the gate, not a key in a drawer

Why a key is the wrong shape for a pipeline, what a run proves instead, and the checks it must pass.

A key is a credential that does not care who holds it. The quick way to let GitHub Actions deploy into a project is to make a key for a service account, a JSON file with a private key inside, and paste it into the repository as a secret. It works on the first try, and it is the wrong shape. The key does not expire unless someone deletes it. It works from any machine it is copied to, so a log line, a careless workflow or a laptop backup that leaks it leaks the deploy rights with it. And nothing in the key says which run used it. The kit's own key check puts it in one line: a key is a credential that does not expire and works wherever it is copied.

Federation swaps the key for proof. GitHub signs a short statement for every job that asks for one: which repository is running, its numeric id, which branch, which workflow. Workload identity federation lets Google trust that signature. The run hands its signed token to Google's token service, which checks it against the rules your lane wrote down in `wif.tf`, and if they hold, issues a credential that expires in about an hour. Nothing is stored in the repository, so there is nothing in it to steal. A token that leaks is useless within the hour, and only that repository's runs, on that branch, can ever get a new one.

Three checks in the condition, and one on the account. The provider's condition in `wif.tf` is three equalities. The repository's numeric id, because a name can be given up and claimed by someone else, and an id cannot. The repository's name, kept so the logs read well. The ref, the branch, because without it anyone who can push a branch to your fork could add a workflow file and deploy. A separate check sits on the account itself: only a federated identity whose repository id is yours may become `sa-documind-cicd`. The kit's comment calls the id and the ref the two checks that tutorials stop before.

A gate pass, not a duplicate key. You could give the electrician a duplicate key to your flat. It opens the door for whoever holds it, on any day, until you change the lock, and you would never know who had it copied. Most housing societies work the other way. The guard at the gate checks the visitor against an entry you approved in advance (which flat, which person, which day) and writes a pass that is void by evening. A service-account key in a GitHub secret is the duplicate key. Workload identity federation is the gate: GitHub vouches for which repository and which branch is at the door, Google's token service checks that against the entries `wif.tf` gave it, and the pass it writes lasts about an hour. Nothing was handed over in advance, so there is nothing to copy.

#### Try it: would this run get a credential?

The panel takes one token, as GitHub would sign it, through the two checks your lane holds: the provider's condition, which Google's token service evaluates at the workflow's auth step, and the binding on `sa-documind-cicd`, which IAM checks when the run first asks for the account's own token. Pick a run, or edit the claims. The last control changes the trust itself, to the repository's name alone, the shape `wif.tf` had before the kit repaired it: first with today's binding by id, then with a binding by name as well.

Your lane's trust, named at lesson 0.3's step 3: repository `YOUR-GITHUB-USER/YOUR-REPO`, id `REPO_ID`, ref `refs/heads/main`.

Built when this page was built, from the kit you clone. The condition is `wif.tf`'s own three lines, joined as Terraform joins them, and the plan guard's parser in `commands/infrastructure.py` accepts it; the binding is the file's `principalSet` member; the mapping copies each claim into the attribute the binding reads. The panel compares strings exactly, as the provider does, and before this page was written node ran it on every run above under all three trusts, and on hand edits, against a Python evaluation of the same text. What the account may do comes from `sa.tf`'s `cicd_roles` and `cicd_actas` and `wif.tf`'s token grants.

Under `wif.tf` as it is, two of the seven runs get a credential: your fork's `main`, and the same run's `promote` job, whose subject names the `production` environment instead of the branch. The condition never reads the subject, so that job still passes. Every other run stops at the auth step. A renamed fork stops too: the name clause fails closed, and the trust has to be changed on purpose. Now switch the trust to the name only. A branch and a tag of your fork get the account, because nothing pins the ref, while the claimed name is still stopped, one step later, by the binding's repository id. Bind by the name as well and whoever claims your old name gets it too. That is the trick `wif.tf`'s comment describes, and the reason both the condition and the binding are keyed on the id.

It calls nothing. A real token is signed by GitHub and carries more claims than these four (the workflow, the commit, the run's id, the actor), and the provider ignores every claim its condition and mapping do not name. The comparisons are exact: a name in another case, a trailing space or a short ref such as `main` fails, as it would at the provider. Step 7 sends a real branch run to your lane's provider and records what it answers.

### The words: federation, OIDC token, claim, pool, provider, mapping, condition, STS, binding, impersonation, key, variable, environment, ref

Fourteen rows, each with the value it takes on your lane.

Hold two questions apart. Who may become the pipeline's account is the trust: one repository, by id and name, on one branch. What that account may do is its roles and the eight accounts it may act as, which lesson 0.3's step 4 laid out. This lesson proves the first. The second is why the first matters: whoever controls the trusted repository's workflows can deploy code that runs as your services.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head. This lesson adds a third, `sa-documind-cicd`, which a GitHub run becomes for about an hour without any key.

The shell from the setup block above, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`, and acme pinned to the kit's index for the dispatch's gate. A GitHub account that owns the repository your lane trusts, which lesson 0.3's step 3 asked you to make a public fork of `netsetos/agents_workshop_learner`. The GitHub CLI, signed in as that account: `gh --version` prints a version (if not, install it from the GitHub CLI's own site), then `gh auth login`. The machine that ran `make plan`, because `make ci-vars` reads the inputs that plan saved; step 5 says what to do on another. About twenty minutes for the dispatch, most of it the build and the live gate.

### Your fork and your project, as GitHub and the console show them

Which repository your lane trusts, whether it can run the workflow, and where Google keeps the trust.

#### Definition

Your lane's trust lives in two places. Google holds it as a provider in a workload identity pool and a binding on the pipeline's account. Your checkout holds the same three values in `terraform/runbook-project.auto.tfvars.json`, which `infrastructure.py prepare` saved at lesson 0.3's step 3 and every plan since has read. The workflow lives in the trusted repository, at `.github/workflows/documind-cd.yml`: the learner repository is the kit itself, so your fork carries it at its root. Before anything runs, three things must hold. The trusted repository is yours and public, its workflows can run, and the console shows the trust you expect.

#### Do it: what your lane trusts, and what GitHub says about it

The cell reads the trust from the inputs file and exports the repository as `GH_REPO`, which every later cell uses. Then it asks GitHub about that repository: whether it is public and a fork, its numeric id, and the state of its workflows.

Read four things. The repository is yours, by name. It is `PUBLIC`: required reviewers on an environment are free on a public repository and need a paid plan on a private one, and step 5 needs one. Its GitHub id equals the id in the trust; if not, the trust names a repository that was deleted or replaced, and every run will be refused at the auth step. And both workflows are `active`. A fork starts with its workflows switched off: open your fork's Actions tab once, press the button that enables them, then run the cell again.

The trust was fixed when the lane was created. `wif.tf`'s three values came from lesson 0.3's step 3, and a later plan that would change them is refused (step 4 shows the lines). If the cell names a repository you do not own, a private one, or the upstream itself, do not try to move it. Read this page's recordings, which show every run on the author's lane and fork, and build and deploy the same candidate as yourself on the local operator path in step 9. Moving a lane's CI trust is a reviewed migration, outside this course.

#### In the browser: GitHub

- Actions, on your fork: `documind-cd` and `DocuMind dry run (Tier A)` in the list of workflows. `documind-cd` runs only when a person starts it, so it has no runs yet.

- Settings > Secrets and variables > Actions: no repository secret, and this lesson adds none. The Variables tab stays empty until step 5.

- Settings > Environments: none yet. GitHub would create `production` the first time a job named it, with no reviewer at all; step 5 creates it first, with you as its reviewer.

#### In the browser: the Google Cloud console

- IAM & Admin > Workload Identity Federation: the pool `documind-github` and, in it, the provider `github-oidc`. Its page shows the issuer, the four attribute mappings and the condition, with your repository, its id and `refs/heads/main` written in.

- IAM & Admin > Service accounts > sa-documind-cicd: the Keys tab lists no key. The Permissions tab lists who has access to the account, and one of them is the pool's set of identities whose repository id is yours.

Nothing changed. You found the one repository whose runs can become `sa-documind-cicd`, checked that GitHub agrees on its id, and saw the same trust in Google's console. Every later step acts through that repository. If a check above failed, the red box says what to do instead.

### What makes it keyless: the trust, the account and the workflow

wif.tf's provider and binding, sa.tf's account, documind-cd.yml's one permission, and the plan guard that keeps the trust where it is.

#### Definition

Four files make the pipeline keyless, and none of them holds a secret. `wif.tf` declares the pool, the provider with its mapping and condition, and the binding that lets a federated identity become the pipeline's account. `sa.tf` declares that account and what it may do. `documind-cd.yml` lets its jobs ask GitHub for a token, which Google's auth action exchanges. `infrastructure.py` keeps the trust from moving once it exists. Read them in that order: who is trusted, as whom, by which workflow, and what stops the trust from drifting.

#### The trust

The mapping copies four claims. `sub` becomes the subject, the name Google's audit log gives the federated identity (step 8), and three become attributes. The condition is the three equalities the panel in step 1 evaluated, written with Terraform variables that your confirmed inputs fill. The issuer is GitHub's own, so only tokens GitHub signs are considered at all.

The binding grants `roles/iam.workloadIdentityUser` on `sa-documind-cicd` to a `principalSet`: every identity in the pool whose `attribute.repository_id` is yours. The condition already pins the same id, so on your lane the binding never refuses a token the condition accepted. It is the second lock, for the day someone loosens the first, and the panel's middle trust showed what it still stops. The two outputs are the values `make ci-vars` reads in step 5.

`deploy_ref` defaults to `refs/heads/main`, and your confirmed inputs set it explicitly. The second resource lets the pipeline mint tokens as exactly two accounts, the UI's and the outsider's, because the live gate on the candidate asks as both. Lessons 4.2 and 4.3 ran that gate from your shell.

#### The account

Five project roles: `roles/cloudbuild.builds.editor`, `roles/artifactregistry.writer`, `roles/clouddeploy.releaser`, `roles/clouddeploy.jobRunner`, `roles/run.developer`. The comments refuse two more: object admin on Cloud Storage, which at project scope would reach the uploads bucket of customer documents and the audit bucket, and log writing. The account may also act as eight named accounts, itself included: `documind-api-sa`, `documind-ui-sa`, `documind-ingest-sa`, `documind-admin-sa`, `documind-chat-sa`, `documind-mcp-sa`, `documind-agent-sa`, `sa-documind-cicd`. They are granted one by one in `cicd_actas`, and lesson 0.3's step 4 shows that list and why it is never one grant on the project. (The comments carry the earlier course's lesson numbers.)

#### The workflow

One permission makes the token possible: `id-token: write`. Without it GitHub mints nothing, and the auth step has nothing to exchange. The dry-run workflow does not ask for it, so its runs, on every push and pull request, never hold one. The auth step names the provider and the account through two repository variables, not secrets, because neither value grants anything to whoever reads it: only a token from your repository, on `main`, satisfies the provider. After it, `make build` and `make release-candidate` are the same targets you could run from your shell, run here as `sa-documind-cicd`. Lesson 4.3 read the two steps that follow: the check that the candidate answers as the tag, and the live gate.

#### The trust, once applied, does not move

Every `make plan` reads the existing provider's condition back from the state, and refuses a plan that would change its condition, mapping, issuer or switch, or the binding's member. A `prepare` that names another repository, id or ref than the applied trust is refused too. That is why the repository you named at lesson 0.3's step 3 is the repository this lesson runs in.

You read every line that makes the pipeline keyless, and there is no secret among them. The four values a run needs are public facts about your lane: the project, the region, the provider's full name and the account's email. What a run must be, not what it must hold, decides whether it gets in.

### Four variables from your lane, and a person in front of production

make ci-vars reads the values the workflow needs, refuses a wrong region, and warns until production has a reviewer.

#### Definition

The workflow reads four repository variables: `GCP_PROJECT`, `GCP_REGION`, `WIF_PROVIDER`, `CICD_SERVICE_ACCOUNT`. `make ci-vars` prints the `gh variable set` line for each, so nothing is typed by hand, after checking that the workflow reads exactly those four. The project and the region come from the inputs your `make plan` confirmed, and a `PROJECT` or `REGION` the lane was not planned with is refused: the Makefile's `REGION` defaults to `us-central1`, and a workflow told the wrong region would build into an image repository that does not exist. The provider's name and the account's email come from `terraform output`, checked against the names `wif.tf` and `sa.tf` give them and against the project. Then, if `gh` is installed, it reads your fork's `production` environment, because GitHub creates a missing environment the first time a job names it, with no reviewer, and `promote` would then move traffic with nobody approving.

#### The code

#### Do it: the first make ci-vars

Four lines to run, the trust they serve, the one dispatch line the trust allows, and a warning on standard error: there is no `production` environment yet. The command only read: `terraform output` in your checkout, and one GET of the environment. If it stops instead, its message names the fix. On a machine other than the one that ran `make plan`, `make tf-backend PROJECT="$PROJECT"` connects the checkout to the lane's state, and `python commands/infrastructure.py prepare --project "$PROJECT" --region "$REGION"` writes the inputs file back from it.

#### Do it: a reviewer, then the variables

The cell creates `production` through GitHub's REST API with you as its one required reviewer (in the browser: Settings > Environments > New environment, then Required reviewers). It runs `make ci-vars` again, pipes the four lines it printed into the shell, and reads back what the repository now holds.

The warning is gone; in its place `make ci-vars` ends on `# production: 1 required reviewer, so promote waits for a person`. The list shows the four variables with your values, and the repository holds no secret. On a team, also set the environment's `prevent_self_review`, so the person who starts a run cannot approve it; alone on a fork, you are both.

#### Change it: the Makefile's region

A shell that never exported `REGION` sends the Makefile's default. The kit refuses it before any tool runs:

Your fork now knows where to deploy and as whom, and it knows nothing that would let anyone else do it. Promote waits for a person, the one gate in the workflow that is not a program. Every value came from the lane and was checked against the others, so a variable set from the wrong checkout, project or region was refused here, instead of failing ten minutes into a run.

### A build and a deploy from main, with no key

One run on your fork: the offline gate, a build, a candidate revision with no traffic, the live gate, then a person.

#### Definition

A dispatch on `main` with `path=candidate` runs three jobs. `eval-gate` runs the offline gate with no credential at all, as every push's dry run does. `release-candidate` needs it to pass, then signs in through the auth step, builds the API's image with `make build`, tagged with the run's commit, and puts it on a new revision of `documind-api` with no traffic and the tag `candidate`. It checks that the candidate answers as that commit, then runs the live gate against it: 65 golden rows, as the roster member and as the outsider. `promote` needs a green `release-candidate` and the approval of the `production` environment's reviewer. Here you say no: lesson 11.2 judges exactly this candidate before anything moves traffic to it, and lesson 11.3 promotes.

#### Do it: dispatch, and wait for the build and the gate

The cell starts the run, finds its id, prints its page, waits until `release-candidate` has finished, and prints the run's summary. Open the page while it waits and watch the jobs and their steps. In the browser the same start is Actions > documind-cd > Run workflow, on `main`, with `candidate` as the path.

A green `release-candidate` is the lesson's proof. Every Google call in it (the build, the new revision, the tokens for the gate) was made as `sa-documind-cicd`, which the run became through the auth step, with no key. `promote` waits for its reviewer. If `release-candidate` is red instead, read its failed step with `gh run view "$RUN" --repo "$GH_REPO" --log-failed | tail -n 30`; step 9 names what the build asks of the account and where the kit grants it.

#### Do it: say no at promote

On the run's page: Review deployments, tick `production`, then Reject. The cell does the same through GitHub's REST API, as the reviewer:

The run ends, and nothing has moved traffic. The candidate keeps its tag and its 0%, which is where lesson 11.2 starts.

#### Do it: what the run left on Cloud Run

The cell reads `documind-api`'s traffic and the candidate revision, then asks GitHub which commit the run built and how the run ended.

Four facts to match. The serving revision still takes 100%, and the candidate takes 0% under the tag `candidate`. The candidate's image is `api:` followed by the run's full commit, and its `GIT_SHA` is the same commit, which is what `/version` reports on its tag URL. The revision was made by `sa-documind-cicd`, not by a person. And the run ended with `promote` rejected.

The workflow's other path cuts a Cloud Deploy release from `run-service.yaml` and rolls it out over `documind-api`. That file sets `AUTH_MODE`, `SELF_URL`, `IAP_AUDIENCE` with a literal `PROJECT_NUMBER` on `us-central1`, so the rollout would replace your API's settings with values that are not your lane's, and break it. `make ci-vars` prints the dispatch line with `-f path=candidate` for this reason, and the candidate path is the lane's release.

A workflow on GitHub's machines built your API's image and deployed it to your project as a revision that serves nobody yet, and at no point did a key exist. GitHub signed a token for the job; Google checked it against `wif.tf` and gave the run an hour as `sa-documind-cicd`; the account's roles let it build and make the revision; the person in front of production said no. Step 7 sends the same workflow from a branch.

### A branch dispatch, refused at the auth step

The same workflow, the same fork, another branch: eval-gate passes, and release-candidate stops before it can call Google as anyone.

#### Definition

A run started on a branch carries `refs/heads/` in its token's `ref` claim, and the provider's third clause wants `refs/heads/main`. So the token service refuses the exchange, and the auth step fails. `documind-cd.yml`'s header says so in advance: a run from any other branch fails at the auth step, and that is the branch gate working, not a misconfiguration. Here is why it matters. Anyone who can push a branch to your fork can change the workflow file on that branch, and a run of that branch uses that branch's file. Without the ref clause, the rewritten workflow would get the same hour as `sa-documind-cicd` that `main` gets.

#### Do it: a branch, a run, a refusal

The cell makes a branch at `main`'s commit through GitHub's REST API, dispatches the workflow on it, waits for the run to finish, prints its summary and the error lines of the failed step, and deletes the branch. In the browser: the branch menu on your fork's code page, then Run workflow with that branch chosen.

`eval-gate` passed: it needs no credential, so the branch makes no difference to it. `release-candidate` failed at its auth step, with Google's refusal in the error line, and the steps after it never ran, so nothing was built and nothing was deployed. `promote` never started. The workflow file, the repository and the commit were step 6's; only the ref differed.

The refusal happened at Google, before any credential existed: the token service read the branch from GitHub's signed token and found the condition false. Nothing in the branch could change that, because the token is GitHub's to sign and the branch is GitHub's to report. To deploy from another branch you would change the trust itself, which `make plan` refuses (step 4).

### What Google holds, and who did what

The provider and the binding over IAM's REST API, the audit trail of step 6's run, and every account's keys.

#### Definition

Three reads close the proof. The provider and the account's policy, read from IAM's REST API as you, show the trust Google enforces, not the trust a file declares. The Admin Activity audit log, which Google writes for every call that changes a resource and which cannot be switched off, shows what `sa-documind-cicd` changed and on whose behalf. And `make keys-check` lists every account in the project with its user-managed keys: the count that must be zero.

#### Do it: the trust and the binding, from IAM's REST API

The condition is the three equalities with your values, as `wif.tf` renders them, and the mapping is its four lines. On the account, `roles/iam.workloadIdentityUser` goes to the pool's identities with your repository's id, and `roles/iam.serviceAccountUser` to the account itself, from `cicd_actas`. The last line asks the same API for the account's user-managed keys, and gets none.

#### Do it: the audit trail of step 6's run

Each entry is a change `sa-documind-cicd` made: the build it submitted, the revision it created. Where Google records the delegation, on behalf of names the federated identity that became the account: the pool, then `subject/` and the job's `sub` claim, with your repository and its ref. A key can never give you that line. Whoever holds a key signs in as the account and leaves no trace of who they are.

#### Do it: zero user-managed keys

The first line says where your project sits. Under an organization, `org_policy.tf`'s `enforce_no_sa_keys` can forbid making keys at all, and an organization created on or after 3 May 2024 forbids it by default. A personal account's project has no organization, nothing can forbid a key there, and this check is the control. Every account follows with its count, and the last line must be `no user-managed keys: no key file can sign in as any account of documind-ai-YOUR-ID`, with exit 0.

#### Change it: what a key looks like to the check

Never make a key to see this. Here is the same command, run when this page was built, against a stand-in project in which `sa-documind-cicd` holds one key, the shortcut this lesson replaces:

Exit 1, the key's id and creation time, never expires, and the delete command. A key that was disabled but not deleted is still listed, and marked so: it can be enabled again.

Google holds the trust you declared, the run is on record as the account acting for your repository's `main`, and no account in the project has a key. The proof of keyless is that zero, not the absence of a JSON file in the repository: a key made last month for a local script would deploy just as well.

### What may stop the first dispatch, the trust that cannot move, and the path without GitHub

What the build asks of the pipeline's account and where the kit grants it, the author's first dispatch, the local operator path, and what each run costs.

#### Each Google call the run makes, and what the kit grants for it

Read the candidate path's calls against `sa-documind-cicd`'s roles, the APIs `make apis` enables and the two grants `make build-access` adds:

None of the five roles is a Cloud Storage role, and none reads logs, on purpose. `gcloud builds submit` uploads the source to the project's Cloud Build bucket before the build starts. Left to choose that bucket, it lists the project's buckets to check the bucket is the project's own, which needs a project-wide storage permission. The workflow names the bucket instead, and `make build-access`, which `make up` runs, gives the account the bucket's legacy writer role on that one bucket. Following the build's log would mean reading Cloud Logging, so the step submits the build `--async` and polls its status, printing a link to the log. Cloud Build runs the build as the project's default compute account, and with Google's default organization policy the account that submits a build must be able to act as that account: `make build-access` grants that too, and refuses on a project whose default account holds Editor or Owner, where acting as it would hand the pipeline the same. `sts.googleapis.com`, the token service, is among the 41 APIs `make apis` enables. A lane made up before these grants gets them from `make build-access PROJECT="$PROJECT"`. The first dispatch on a real lane proves them, so the author runs it before this lesson is taught:

If a dispatch of yours still stops at a permission or an API, the failed step's last lines name it. The fix belongs in the kit, as a grant in `sa.tf` or `build-access.sh`, or an API in `make apis`, so report it to the course team rather than granting a broad role by hand. Meanwhile the local operator path below builds and deploys the same candidate.

#### The trust you named at lesson 0.3 is the trust you have

The provider's condition and the binding were written when `make up` first applied `wif.tf`, from the three values lesson 0.3's step 3 confirmed, and step 4's lines refuse any plan that would change them. A fork renamed after that day fails the name clause, and a fork deleted and made again gets a new id and fails the id clause: either way every run is refused until the trust is migrated, deliberately. If your lane trusts a repository you cannot run Actions in, this page's recordings and the path below are your lesson.

#### Without GitHub: the local operator path

The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag `candidate`. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the `candidate` tag to the revision it makes, so run it only if step 6 could not run.

Your checkout now holds `.candidate-revision`, the name `make promote` would move traffic to. The dispatch's job kept that file on GitHub's runner, and passed the name to `promote` as a job output instead.

#### What it costs

The gate's usage rows price generation only: the query embedding and the Ranking API bill on their own lines. `make usage PROJECT="$PROJECT" HOURS=1` after the dispatch prints what the gate's answers cost on your lane.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

On your fork: the `production` environment with you as its reviewer, the four repository variables, and two runs in the Actions history, step 6's with `promote` rejected and step 7's failed at auth. The branch `try-a-branch` is gone, and no secret was added. In Artifact Registry: one more image, `documind/api:` with the run's commit. On Cloud Run: one more revision of `documind-api`, made by `sa-documind-cicd`, tagged `candidate`, taking no traffic; the serving revision is unchanged. In Cloud Build, one build submitted by the same account; in Cloud Logging, the gate's usage rows under the candidate's revision, and the audit entries step 8 read. Keep the candidate: lesson 11.2 judges exactly that revision. If you stop here instead, `gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate` removes its URL. Put acme's pin back now, with the setup section's pin-back window.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.1 Build and deploy using keyless identity · v5.0

Next: Lesson 11.2 Evaluate and gate the exact candidate revision.
