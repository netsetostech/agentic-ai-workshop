# Lesson 4.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.7_Access_Tests_WIX.html`, reviewed at blob `af7968ba7b37b06283c139e316adcd2049e9156c`. Learners read that page on the course site; this guide keeps its prose.

Lesson 4.6 traced how a request becomes an identity and a tenant. This lesson tests it. You send four requests side by side and get the door's refusal, a 401, a 403 and an answer. You ask every isolation row twice: as the outsider, who must be refused each time, and as a member, whose answers must never carry another tenant's marker. Then you pin a tenant that must keep its text in India to a store outside India, and read the usage row that shows the policy won.

- Four answers a request can get, and the walls between tenants

- The words: the door, 401, 403, outsider, isolation row, the two walls, data_region, pin, policy_fallback

- Before you run anything: set up the shell

- The refusal ladder: the door, a 401 and a 403 side by side

- Cross-tenant: every isolation row, as the outsider and as a member

- Residency: each tenant's data_region, and the rule that applies it

- The policy against a pin: a tenant kept in India, pinned to a store outside it

- The kit's own tests of the same refusals

- Why the tests are shaped this way, and what they cost

- Verify it yourself: the checklist

You will learn what each refusal means and where it comes from, why a test suite must assert refusals and not only answers, and how the kit keeps one tenant's text away from another and inside the region its policy names. Then you will prove it on your lane: a 401 and a 403 side by side, the outsider refused on every isolation row, a member's answers free of every other tenant's marker, and a residency policy overruling a pin.

### Four answers a request can get, and the walls between tenants

Each refusal comes from a different check, and a test is only useful if it can tell them apart.

A request can get four answers, and each means something different. A refusal at the door comes from Cloud Run itself, before any kit code runs: the caller brought no token, or an account the service does not admit. A 401 from the API means a token reached it but proved nobody: no email, the wrong audience, a forged assertion. A 403 from the API means the API knows exactly who is asking, and that identity is not on the tenant's roster. A 200 means all three checks passed. A test that only checks for the 200 cannot tell an open service from a closed one, which is why the kit's smoke test asserts a refusal too.

Two walls stand between tenants. The first is the roster: an identity may ask only for the tenants whose rosters list it. The second is the retrieval filter: every vector query is restricted on `tenant_id`, and the Firestore rung carries the same equality, so even an identity on two rosters gets only the named tenant's chunks. The isolation rows test both walls. The outsider asks each one and must be refused. A member asks each one, and the answer must not carry the marker that only another tenant's documents hold.

The outsider is a fixture built to fail in one place. IAM admits it, with `roles/run.invoker` on the API, and no roster lists it. So its refusal has to come from the roster, as a 403, and never from the network. A 401 or a door refusal for the outsider would mean the test proved nothing about the roster. It is never admitted to the A2A peer, which has no roster of its own to refuse it with.

Residency is a third wall: where a tenant's text may be held. `tenant_settings/{tenant}.data_region` says `in`, meaning the kit's own rows in India and nothing else, or `any`, meaning a managed store outside India may hold a copy. An absent policy means `in`. If a tenant marked `in` is pinned to a managed store, the API overrules the pin on every request. It serves from its own index instead, and writes `policy_fallback` 1 on the usage row. Only the operator writes either field.

A bank's locker hall. No card, and the guard at the gate turns you away: the door. A card that names nobody is refused at the counter: the 401. A known customer who has no locker in this branch is refused too, politely and by name: the 403. Inside, your key opens only your locker, even if you rent two: the retrieval filter. And some customers' valuables never leave the city vault, whatever a form elsewhere says: residency.

#### The test plan: every identity against every tenant, and where a tenant's text is searched

The matrix is what this lesson's tests should find. Each cell is one identity asking one tenant, and a tap shows its path through the door, the verifier and the roster. The panel below it applies a tenant's policy and pin the way the API does.

The matrix is computed from the invoker list in `commands/lesson-12.2.sh` and the plan `make roster` writes. The residency panel ports the pin rule in `choose_for()` and all of `retrieval_backend_for()`. For all 72 combinations of its choices, the build ran the kit's own two functions, and the panel had to agree with each.

It is the plan, not your lane. Your rosters may list more people, and an operator can bind the invoker role more widely. The tests in steps 3 and 4 are what check the lane itself. The panel shows the store the API would search; it cannot tell you whether that store holds your documents.

### The words: the door, 401, 403, outsider, isolation row, the two walls, data_region, pin, policy_fallback

Ten rows, each with the value it takes on your lane.

One distinction to hold: the roster and the filter guard against different mistakes. The roster stops the wrong identity from asking at all. The filter stops the right identity from reading the wrong tenant's chunks. Lesson 4.2's gate tests the first with the outsider; the member's answers in step 4 test the second.

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

The shell, in the kit's folder, with `API`, `tok` and `otok`. Step 6 writes one setting, a tenant's pin, and clears it in the same cell. Everything else only reads or asks questions.

### The refusal ladder: the door, a 401 and a 403 side by side

The same question four times, with no token, a token that proves nobody, the outsider's token and a member's token.

#### Definition

Each rung fails a different check. With no token, Cloud Run refuses at the door and the API never sees the request. A token minted without `--include-email` passes the door, because Cloud Run needs only a valid token for the service. The API's bearer leg then refuses it, because it names nobody: that is the 401. The outsider's token passes the door and the verifier, and the roster refuses it: that is the 403. The member's token passes all three and gets an answer. The cell prints each status beside the body's first characters, so the two refusals the API writes are on the screen together.

#### The code

#### Do it

Four requests, four checks. The first never reached the API: Cloud Run answered with its own page. The second reached the API with a genuine Google token and was refused as a 401, because a token without an email proves no identity. The third came from an account IAM admits, and the roster refused it as a 403 with the API's own sentence. That 403 is the outsider working as designed: the refusal came from the roster, the one place that decides tenants. The fourth was answered. The 401 and the 403 side by side are this lesson's first proof.

### Cross-tenant: every isolation row, as the outsider and as a member

The roster wall with `check_isolation()`, then the filter wall with a member's answers.

#### Definition

The cell runs the live gate's own `check_isolation()` on the 11 isolation rows: the outsider asks each one, and anything but a 403 is printed as a failure. Those requests stop at the roster, so they cost no model call. Then it asks each row again as `documind-ui-sa`, which is on all three rosters, so the roster lets every question through. Now only the retrieval filter stands between the question and another tenant's chunks. The answer must not contain the row's marker, the figure or phrase that only another tenant's documents hold. `contains()` matches the figure on its own boundaries and in any spelling, so a leak written as `15 days' wages` is caught as surely as `fifteen days' wages`.

#### The code

#### Do it

The outsider was refused on every isolation row, which is `isolation_403_rate` 100%, the value the live gate requires. The member got every question through the roster, and every answer came from the named tenant's own chunks. Zeta's travel cap came back as zeta's, and the rows that only another tenant could answer came back refused. No marker appeared in any answer. A marker here would be close to impossible given the filter, which is exactly why the live gate treats one as exit 2: if it happens, something far worse than a quality regression has gone wrong.

### Residency: each tenant's data_region, and the rule that applies it

The policy's two values, the fail-closed reading, and where the API holds a pin against it.

#### Definition

A tenant's policy is one field of `tenant_settings/{tenant}`, the same document that holds its pin. `policy_of()` reads it strictly: `any` only when the field says exactly that, and `in` for anything else, including a missing field, an unknown value, a missing document or a failed read. `permits()` is the whole rule: `any` permits every store, and `in` permits only a store in an Indian region. None of the managed stores is in India today, since RAG Engine is in us-central1 and Vertex AI Search is global. The API applies the rule per request. The worker applies it when it decides whether to mirror a tenant's documents into those stores. `make roster` writes the demo's policies: acme and zeta `any`, globex `in`.

#### The code

#### Do it: the three policies

Each line is one read of `tenant_settings`, normalised by the same `policy_of()` the API uses. Globex prints `in`: its text may be searched only in the kit's own rows. A tenant whose policy was never written also prints `in`, because the strict reading is the default. That is the property to check first on any residency control: what happens when nobody set it.

### The policy against a pin: a tenant kept in India, pinned to a store outside it

A pin set, a minute's wait, one question, its usage row, and the pin cleared.

The cell pins globex to `rag_engine`, a managed store in us-central1, then waits a minute, because the API reads each tenant's settings once a minute. It asks one of globex's own questions and reads the question's usage row: which backend served, and `policy_fallback`. Then it clears the pin. `RETRIEVAL_BACKEND` is given on each `make` line on purpose, because a value exported in your shell would otherwise win.

The pin said RAG Engine, and `choose_for()` took it, because the pin names a real backend and the mode is dense. `retrieval_backend_for()` then held it against globex's policy, `in`. It served the question from the deployment's own index instead, and the row recorded both facts: the backend that really served, and `policy_fallback` 1. No text went to us-central1, and no error reached the caller. A day of such fallbacks is a count on the usage rows, which is how an operator finds a pin that contradicts a policy. The pin is cleared, so globex is as it was.

### The kit's own tests of the same refusals

The smoke test's check 3b, and the chat service's check 4.

The kit asserts these refusals itself, so a deploy that opened a door would fail its own smoke test. `smoke/smoke.py` sends its question again with no token and passes only on 401 or 403. `smoke/smoke_chat.py` asks the chat service as the outsider and passes only on a 403 from the roster, not a 401 from the verifier. The MCP server's smoke test does the same. The cell runs the API's smoke test and keeps two of its lines.

### Why the tests are shaped this way, and what they cost

The design choices behind each test, from the kit's own comments.

- A refusal is asserted, not assumed. A smoke test made only of "does it work?" passes on a service that answers everybody. Check 3b exists so a deploy that dropped `--no-allow-unauthenticated` fails.

- The outsider is admitted by IAM on purpose. If IAM refused it, every isolation test would pass at the door and prove nothing about the roster. Its invoker role is bound per service, and never on the A2A peer, which has no roster. When it was granted project-wide, the outsider could read acme's documents through that peer.

- The live gate's isolation threshold is the 403, not the marker. The filter makes a leaked marker close to impossible, so a test that waited for one would pass by luck. The leg that can really leak is identity to tenant, and the outsider tests exactly that.

- Every residency default is the strict one. An absent policy, an unreadable one, an unknown value: all are `in`. An unknown pin, or a managed store under hybrid mode, is ignored with a log line, never a 500.

- Only the operator writes a policy or a pin. A service that could widen its own tenant's region could move its text anywhere, the same reason no service writes the roster.

#### What it costs

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Globex's pin was set and cleared in step 6, so `tenant_settings/globex` is as it was, apart from the time stamp of the last change. The usage rows of about fifteen answered questions, and the refused requests in the API's log. No roster, role or policy changed. Lesson 4.8 turns from who may read to what may be read: the PII scan on every document, Model Armor on both sides of the model, and the audit trail an operator can show.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.7 Test valid access, denied access and cross-tenant requests · v5.0

Next: Lesson 4.8 Exercise DLP, guardrails and audit behavior.
