# Lesson 4.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.6_Identity_Tenancy_WIX.html`, reviewed at blob `68df6795d0127a075315d621003ac5db51aa9805`. Learners read that page on the course site; this guide keeps its prose.

Every answer the API gives is for someone, about one tenant's documents. This lesson follows a request through the three checks that decide both. Cloud Run's IAM decides who may knock at all. The kit's shared verifier decides who is asking, from a person's forwarded sign-in or the caller's own token, never from a header. The roster in Firestore decides which tenant that identity may read. You will read each check's settings on your lane, list the rosters, send a request with a forged header, and find the usage row that names the verified caller anyway.

- Who is asking, and which tenant may they read

- The words: ID token, audience, assertion, the two legs, SELF_URL, the door, roster, 401 and 403, the row's user

- Before you run anything: set up the shell

- The door and the verifier: who may knock, and what makes a token count

- The roster: one document per member, two ways to read it, one writer

- The surfaces: who calls the shared verifier, and who still keeps a copy

- One request, end to end: a forged header, and the row that ignores it

- The person's leg: how a signed-in person reaches the API through the UI

- How identity went wrong before, and what each check costs

- Verify it yourself: the checklist

You will learn the difference between proving who is asking and deciding what they may read, and why the kit keeps them in two separate places. You will learn what a token must carry to count, and why a header never counts. Then you will prove it on your lane: the API's audiences and invokers, the claims in your own token, the three rosters, and a usage row that names the verified caller even when the request claims to be someone else.

### Who is asking, and which tenant may they read

Three checks in a row: the door, the verifier and the roster. Each can refuse, and each refusal means something different.

Three checks stand between a request and a tenant's documents. The first is Cloud Run's own IAM, before any kit code runs. It admits a request only when it carries a Google ID token from an account holding `roles/run.invoker` on the API, and 4 accounts do. The second is `shared/iap.py`, which decides who is asking. The third is `shared/tenancy.py`, which decides whether that identity is on the roster of the tenant the request names. Only after all three does retrieval begin.

The verifier has two legs, and it tries them in a fixed order. A person signs in at IAP in front of the UI, and the UI forwards the person's signed assertion to the API beside its own token. When an assertion is present, it is the only leg tried: it must be signed with IAP's keys, minted for one of the API's accepted audiences, issued by IAP, and carry an email. With no assertion, the caller's own ID token is the identity: it must be minted for the API's own URL, `SELF_URL`, and carry a verified email. That second leg is how `run_eval.py`, the smoke tests and an agent in a notebook are known, since nobody signed in for them.

A header is a claim, not a credential. Anything that can reach the service can set `x-user-email` or `x-tenant-id`, and the API once read both. Now it reads neither. The tenant is something you are, on a roster the operator writes, and not something you send. The same rule gives the two refusals their meanings. A 401 says the API does not know who you are. A 403 says it knows, and you may not read that tenant.

The usage row names the verified caller. Every answer writes one row with the tenant and a `user` field, taken from the verifier and never from a header. So the bill, the audit and the per-tenant numbers all name the identity the checks accepted: the person, when a surface forwarded one, and the calling account otherwise.

An office building. The gate guard lets in only people whose badge names a company in the building. That is the door. At the security desk, a visitor pass printed by reception names the visitor; staff without a visitor present their own card. That is the verifier, and the pass beats the card because it names the person actually walking in. Each floor keeps a list of who may enter, written by the building office. That is the roster. A sticky note saying "I work on the fifth floor" opens nothing.

#### The identity tracer: one request, through the door, the verifier and the roster

Choose what the request carries and which tenant it names. The tracer follows it through the three checks, with the kit's own messages, to its HTTP status and its usage row. It uses the API's real settings and the rosters `make roster` writes.

The door is the invoker list in `commands/lesson-12.2.sh`. The verifier and the roster are `shared/iap.identity()` and `make roster`'s plan, ported. For all 360 combinations of the choices above, the build ran the kit's own `identity()`, with Google's signature check faked and google-auth's real exception classes raised, and the tracer had to agree with every verdict and message.

It checks no signature; a real token either verifies or does not, and the tracer takes your word for which. Cloud Run's own refusal of a request without a token is a 401 or a 403 depending on the case, which is why the kit's smoke test accepts either. Your lane's rosters may hold more people than `make roster`'s plan; step 4 lists them.

### The words: ID token, audience, assertion, the two legs, SELF_URL, the door, roster, 401 and 403, the row's user

Eleven rows, each with the value it takes on your lane.

One distinction to hold: authentication and authorisation live in different files, owned by different people. The verifier proves who is asking, and nobody configures it per person. The roster says what they may read, and the operator writes it. An account can pass the first and fail the second, and the outsider fixture exists to prove exactly that.

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

The shell, in the kit's folder, with `ME`, `API`, `tok` and Application Default Credentials, which the Firestore reads in step 4 need. Everything here only reads, except the two questions in step 6. Nothing writes a roster.

### The door and the verifier: who may knock, and what makes a token count

The invoker binding, the verifier's two legs in the kit's code, the API's two settings, and the claims inside your own token.

#### Definition

The deploy script grants `roles/run.invoker` on documind-api to 4 accounts and nobody else. The UI's account streams answers and runs the smoke tests. The chat service and the MCP server reach the API through the one retrieve tool. The outsider is the eval gate's fixture, admitted so that its refusal comes from the roster and not from the network. Past the door, `identity()` runs. An assertion, if present, goes through `verify()` against every audience in `IAP_AUDIENCE`. Otherwise the bearer token goes through `bearer_email()`, which requires `SELF_URL` as the audience and a verified email. Every failure is an `IapError`, which the API turns into a 401.

#### The code

#### Do it: the API's audiences, and who may invoke it

#### Do it: what your token says about itself

The cell mints two tokens for the API as `documind-ui-sa`: one the way `tok` does, and one without `--include-email`. It reads their claims without verifying them; the API does the verifying. Nothing is sent.

The API accepts assertions minted for exactly two services, the UI and the chat service, and bearer tokens for exactly one audience, its own URL. Four accounts may knock. Your token carries that audience, the account's email and `email_verified`, so the bearer leg accepts it. The second token has the same audience and no email at all, and `bearer_email()` refuses it with `the bearer token carries no verified email`. That is why `tok` passes `--include-email`, and why a token minted any other way gets a 401 that looks like a broken login.

### The roster: one document per member, two ways to read it, one writer

The two readers, the operator's writer, the three rosters on your lane, and the plan `make roster` would write.

#### Definition

A member is one Firestore document, `tenants/{tenant}/members/{email}`, keyed by the email and carrying it as a field. The key makes the API's question one read: is this identity on this tenant? The field makes the UI's question one query: which tenant is this person on? The reverse lookup returns the first match, because in DocuMind a person belongs to one customer. No service writes the roster. `make roster` runs `commands/lane.py roster`, which puts the members you name on one tenant and the service accounts on the tenants they serve. The UI's, the chat service's and the MCP server's accounts go on all three golden tenants, the A2A peer's on acme only, and the outsider on none.

#### The code

#### Do it: the three rosters, as Firestore holds them

#### Do it: the plan `make roster` would write for you

`make roster` runs this command without `--dry-run`. The dry run prints the memberships and the data-region policies it would set, and writes nothing.

You read the rosters the API consults on every request. The service accounts sit where the plan puts them: three on every golden tenant, the peer on acme, and the outsider nowhere. You are on acme, as lesson 1.1 left you. The dry run shows the same memberships a real run would write, plus a data-region policy per tenant, which lesson 4.7 uses. A roster that differs from the plan is not wrong in itself, but every extra member is someone who can read that tenant, so read the list the way an auditor would.

### The surfaces: who calls the shared verifier, and who still keeps a copy

The API's two checks, the UI's two credentials, and the two surfaces that still verify on their own.

#### Definition

`shared/iap.py` opens by listing four surfaces that once had four answers to "who is asking". The API, the chat service and the MCP server now call its `identity()`. The API follows it with `enforce_membership()`, a point lookup that turns a mismatch into a 403. The UI and the admin console still verify on their own. The UI's image copies only its own folder, so it cannot import `shared/`. The admin console's image does copy `shared/`, and its `auth.py` still carries its own check: the same library and key endpoint, failing closed the same way, then its admin list. Only the change has not been made. The UI's copy verifies the assertion with a different library, and finds the tenant with its own reverse lookup, uncached since 12 September. It also still parses its admin list the way `shared/iap.py`'s own docstring calls a bug: an unset list holds the empty string. That is harmless after the login gate, because a verified email is never empty, but it is one fix waiting to be made in two places.

#### The code

#### Do it: which services call the shared verifier

Three services call one verifier, so a fix to it lands in all three at once. The UI does not call it, and it does not need to for the API's sake: every call the UI makes carries its own token for the door and the person's assertion for the verifier, and the API verifies the assertion itself. What the UI's own copy decides is the UI's own business: the admin page, the tenant in the sidebar, and the tenant folder an upload is written to. So the API's answers stay correct whatever the UI's copy does, and the copy still matters, because it decides where the UI writes.

### One request, end to end: a forged header, and the row that ignores it

Two questions to acme, one claiming to be the CEO, and the two usage rows they leave.

The cell asks the same question twice with `run_eval.py`'s own `ask()`, which sets an `x-user-email` header on every request. The first names the eval account; the second claims to be `ceo@acme.example`. Both carry your token and no assertion, so the bearer leg names the caller. After twenty seconds for the logs to land, the cell reads the two newest query rows for acme.

Both questions were answered, and both rows name `documind-ui-sa`, the account whose token the requests carried. The header claiming the CEO is not in either row, because nothing in the API reads it outside the local dev mode. The tenant on each row is the one the request named and the roster allowed. That pair, the verified identity and the tenant, is this lesson's proof. It is also what every per-tenant number in the course is grouped by, from lesson 4.2's rupees to Module 11's reports.

### The person's leg: how a signed-in person reaches the API through the UI

IAP in front of the UI, the assertion forwarded beside the UI's token, and every caller the API recorded in a day.

A person never calls the API directly. They sign in at IAP in front of the UI, which admits only accounts granted the sign-in role. IAP hands the UI a signed assertion with every request. When the UI calls the API, it sends two credentials, as its `_headers()` shows in step 5: its own token, which gets past the door, and the person's assertion, forwarded unchanged. The API's verifier sees the assertion first and takes the person's email from it. The roster check and the usage row are then about the person, which is what lesson 3.8 saw in Chat. The cell counts every caller the API recorded in the last day.

Two kinds of caller share the API, and the rows keep them apart. Your shell, the gate, the judge and the smoke tests appear as `documind-ui-sa`, because no person was forwarded. Questions asked in the UI appear under your own email, because IAP signed you in and the UI forwarded your assertion. If your email is missing, you have not asked in the UI today. A person on no roster would reach the verifier and stop at the roster: they can sign in, and they still cannot read a tenant.

### How identity went wrong before, and what each check costs

The kit's own history, from its docstrings, and why each fix is where it is.

#### Six mistakes the kit made, and the check that now stands in each place

- The API believed headers. It read `x-user-email` and `x-tenant-id`, so anyone who could reach it could claim any tenant. Now the tenant comes from the roster and the identity from the verifier.

- The UI used the Google subject id as the tenant. Every person became their own tenant, colleagues could never share a document, and the roster was bypassed. Now it looks the person up on the roster.

- The UI cached the tenant for five minutes. A person taken off a roster kept their tenant, and the upload right with it, on every instance that had answered them. It has been uncached since 12 September.

- The chat service believed the request body. The caller picked the tenant. It now calls the shared verifier.

- The invoker role was granted project-wide. Every account could knock on every service, and the outsider could read acme's documents through the A2A peer, which has no roster of its own. Since 12 September the role is bound per service, for the callers that need it.

- A token minted for a candidate's tag URL was refused on every row. The API verifies bearer tokens against its canonical URL, whichever URL was called. Minting for `$API` is the fix, and it is why lesson 4.4 used `tok "$API"` against the candidate.

#### Two details that produce a permanent 401

An IAP audience is `/projects/PROJECT_NUMBER/locations/REGION/services/SERVICE`: a leading slash, and the project's number, not its id. Get either wrong and every sign-in fails as if the login were broken. And a service-account token minted without `--include-email` has no email, which the bearer leg refuses. Both failures happen before any tenant is looked at, which is why they are 401s.

#### What it costs

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing but the usage rows of step 6's two questions. No roster was written, no role was granted, no setting changed. The dry run in step 4 printed a plan and wrote nothing. Lesson 4.7 turns these checks into tests: a request with no token, the outsider refused by the roster with a 403 rather than a 401, acme asking for zeta's documents, and each tenant's data-region policy.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.6 Trace authenticated identity into tenant membership · v5.0

Next: Lesson 4.7 Test valid access, denied access and cross-tenant requests.
