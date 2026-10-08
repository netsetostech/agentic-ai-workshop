# Lesson 11.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.6_Cost_Controls_WIX.html`, reviewed at blob `7d2d39676abfdd32aca8e43689880c544e1b0219`. Learners read that page on the course site; this guide keeps its prose.

DocuMind spends money on three clocks. Every answer costs a model call, the month adds up the whole project's bill, and every hour an instance stays up it is billed. Each clock has its own control. The router sends each question to the cheapest model that can answer it, and a breaker reads the month's spend and stops choosing Pro at 80 percent. The billing budget emails the billing admins as the month's bill passes its lines. The off switch floors the GPU services, the gateway and the UI to zero instances every night at 23:00, and `make off` does the same by hand.

In this lesson you read all three as the kit writes them down. You replay 85 percent on a candidate revision that takes no traffic, and watch the model tier change. Then you turn the lane off and watch its instances go to zero.

- Three clocks, three controls

- The words: tier, classifier, breaker, counter, replay, billing budget, floor, quota cap

- Before you run anything: set up the shell

- The controls, as the kit writes them down

- The month so far

- The tier at 85 percent

- Off at night, and the ceiling under it

- Why the controls look like this, what they cost, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn which control acts on which clock, what each one does and does not do, and why none of them turns DocuMind off. Then you will prove two things on your lane:

- at 85 percent of the month's budget, the router sends a worked question to flash instead of Pro;

- after `make off`, the lane's instances go to zero.

### Three clocks, three controls

Per answer, per month and per hour: what spends, and what holds it back.

Per answer: the router and the breaker. With `ROUTING=on`, rag-api first asks `gemini-3.1-flash-lite` to label the question SIMPLE, MEDIUM or COMPLEX (`router.classify()`). Then `breakers.choose_model()` picks the model from the label and the month's spend:

- normal: SIMPLE goes to flash-lite, MEDIUM to flash, COMPLEX to Pro;

- strict, from 80 percent of the month's cap: COMPLEX goes to flash and everything else to flash-lite. Pro is never chosen.

The spend is the API's own counter: one Firestore document per month, `budget/`, which every answer adds its cost to, divided by `BUDGET_USD` (100 dollars on the lane). `SPEND_PCT` replaces that reading, so you can see what the lane does at 85 percent without spending it. On the lane, `ROUTING` is off, and every question goes to `GENERATOR_MODEL`.

Per month: the billing budget. This is a different number. Cloud Billing's budget covers the whole project (Cloud Run, Firestore, the index, BigQuery and the models) in the billing account's own currency: 5,000 by default, which is rupees on an Indian account. It emails the billing admins at 50, 80 and 100 percent of actual spend, and when the forecast passes 120 percent. It changes nothing on the lane.

Per hour: floors, the off switch and the ceiling. A service's `min-instances` keeps instances warm while it is idle: the UI at one on a session day, or a GPU service at one, which costs Rs 121 an hour. Three controls hold this in check:

- the `documind-off` job floors four services to zero at 23:00 IST every night, and `make off` does the same by hand;

- `make gpu-cap` caps the region's L4 quota at one card, so no service can get a second;

- `alerts.tf`'s `gpu_left_warm` pages when a GPU instance stays up for two hours.

None of them turns DocuMind off. `breakers.py` explains why: a budget alert that takes the service down "converts a finance problem into an outage." The controls make the lane cheaper, slower to start, or quieter; it stays up. `make down` removes the lane altogether. That is the end of the course, not a control, and this lesson does not run it.

A company's travel desk, and the office's power. The travel desk books each trip in the cheapest class that works: economy for a one-hour hop, business only for an overnight flight with a meeting on landing. Once the quarter's travel budget passes 80 percent, business class comes off the menu, and people still travel. Finance's budget report is a different number: every expense, not only travel, and all it does is send a letter. At night the facilities timer switches the air conditioning off at 11, whoever forgot. Under all of it sits the sanctioned load on the electricity connection, a ceiling no timer can lift. Those are the router, the breaker, the billing budget, the off switch and the quota cap.

#### The router at any spend

Choose whether routing is on, the class the classifier gave a question, and the month's spend. The panel shows the routing mode, the model chosen, what a typical answer costs, and what happens at 100 percent.

The choice is `breakers.choose_model()`, ported to this page. A check at build time compares the port with the kit's function at 2410 points: every class, every half percent from 0 to 120, with ROUTING on and off. The rates are `cost.py`'s; the typical answer is 2,000 tokens in and 300 out.

It shows the kit's rule. On your lane the classifier decides the class, and the rupees are your own answers'.

### The words: tier, classifier, breaker, counter, replay, billing budget, floor, quota cap

Ten rows, each with the value it takes on your lane.

One distinction to hold: the breaker and the billing budget are two budgets. The breaker reads the API's own model spend in dollars; the billing budget reads the whole bill in the account's currency. Neither knows the other.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `ME` set.

- Step 5 makes a candidate revision that takes no traffic, asks it six questions (a worked question goes to Pro once), then takes the candidate's variables off and drops its tag.

- Step 6 puts a floor of one on the UI for a few minutes, runs `make off`, and lowers one GPU quota. `make gpu-cap-off` puts the quota back.

### The controls, as the kit writes them down

The routing table, run; the counter and the replay; the billing budget's lines; the night switch and the ceiling.

#### Definition

The cell imports `breakers.py` and runs `choose_model()` for each class at six spends. Then it reads the rest from the kit's own files:

- the classifier model, from `router.py`;

- the lane's `ROUTING` and `BUDGET_USD`, from `lesson-12.2.sh`;

- the billing budget's lines, from `budget.tf`;

- the night switch, from `off.tf`;

- the GPU cap, from the `Makefile`.

It also checks whether anything reads `BUDGET_FLOOR_PCT`. Nothing is called.

#### The code

#### Do it

- Two thresholds, and only one acts. At 80 percent, routing turns strict: the MEDIUM column drops to flash-lite and the COMPLEX column to flash. `BUDGET_FLOOR_PCT = 100` is read by nothing, so the comment's min-instances 0 at 100 percent never happens.

- Two budgets. The counter is the API's model spend in dollars. The billing budget is the whole project in the account's currency, and it only emails.

- The night switch knows four services. They are the three GPU-shaped ones and the UI, and `make gpu-cap` puts one card's ceiling under all of them.

If `choose_model()` changes, this table changes with it.

### The month so far

The service's settings, the counter, the billing budget and the GPU quota, read and changed in nothing.

#### Definition

The cell reads documind-api's `ROUTING`, `BUDGET_USD` and `SPEND_PCT` from Cloud Run, and this month's counter from Firestore. From those it works out the spend the breaker would read. Then it asks Cloud Billing for the project's budget.

- This needs `billing.budgets.list` on the billing account. If you do not administer the account, the cell says so and moves on.

- `make gpu-quota` then lists the GPU quotas Cloud Run has in `us-central1`.

#### Do it

- ROUTING is off on the live service, so this month's spend decides nothing yet. If routing were on, a spend under 80 percent would read normal.

- The billing budget watches another number, in rupees on an Indian account, and it would email long before the lane noticed anything.

- The L4 quota is at its default. The quota's names and limits come from your project, not from the kit.

### The tier at 85 percent

Three questions to a candidate with routing on, the same three at a replayed 85 percent, then the candidate undone.

#### Definition

A candidate is a revision tagged `candidate` that takes no traffic, so the live service keeps answering as before.

- The first update turns `ROUTING` on for the candidate. `make candidate` can set `ROUTING` but not `SPEND_PCT` (step 7), so this is a `gcloud` update.

- `ask133` sends it three acme questions as `documind-ui-sa` (a lookup, an explanation, and a worked sum over the travel cap), and prints the model each answer names.

- The second update replays 85 percent with `SPEND_PCT=85`, and `ask133` asks the same three again.

#### Do it: routing on, the month as it is

The candidate read the real counter, well under 80 percent, and routed normally: the lookup to flash-lite, the explanation to flash, and the worked sum to Pro. Each answer names its model. The class itself is recorded nowhere, neither on the answer nor on the row.

#### Do it: the same three at 85 percent

The same questions, with the breaker reading 85: the explanation went to flash-lite and the worked sum to flash. The lookup stayed on flash-lite, because the cheapest tier has nowhere lower to go.

That is the first proof: the model tier changes at 85 percent. On the stand-in, the worked sum cost Rs 0.16 on Pro and Rs 0.11 on flash, and the answer was the same. On your lane, compare flash's answer with Pro's: a worked sum is exactly the kind of question the classifier sends to the top tier.

#### Do it: undo the candidate

Environment variables carry over from one revision to the next. Without the first line, the next `gcloud run services update` would take `SPEND_PCT=85` into a revision that serves traffic. So the variables come off the service's template, the tag is dropped, and the live revision is still at 100 percent, as it was throughout.

### Off at night, and the ceiling under it

A session-day floor, `make off`, the nightly job's entry, the instances at zero, and one card as the ceiling.

#### Definition

A session day puts a floor of one on the UI, so the first learner of the morning does not wait for a cold start.

- The first line sets that floor.

- `make off` then runs its four switches: `slm-off`, `vllm-off`, `gateway-off` and the UI's floor. It removes the Autopilot workload, if there is one, and prints each service's floor. On a lane that never deployed the GPU services, their switches fail and are ignored, and those services read `absent`.

- The last line reads the nightly job's entry in Cloud Scheduler: its schedule, its time zone, its state and its last run.

#### Do it: the floor, then the switch

`make off` floored the UI from one to zero, and the GPU-shaped services are absent on a Core lane. The last line is the 23:00 job: `0 23 * * *` in Asia/Kolkata, enabled, with the time it last ran. It floors the same four services every night whether or not anyone runs `make off`.

#### Do it: the instances, after fifteen minutes

A floor of zero lets the service scale to zero, but an idle instance can stay up for up to fifteen minutes after its last request. The cell waits, then reads the UI's instance count from Cloud Monitoring for the last half hour, a sample a minute.

One idle instance stayed up while the floor held it, and after `make off` the count went to zero and stayed there. That is the second proof: zero instances after `make off`. If yours still reads one, the instance has not been idle long enough; run the cell again.

#### Do it: the ceiling

`make gpu-cap` writes a consumer quota override on the L4 quotas in `us-central1`, capping them at one card. `--max-instances` belongs to one service. The quota belongs to the project, so a second GPU service, a GPU candidate or a typo cannot allocate a second card. Lowering a quota needs no approval; raising it again does.

The L4 quota in `us-central1` now reads `effective 1`, with the default beside it and the override that set it. `make gpu-cap-off` removes the override. Keep the cap unless you run more than one GPU service on purpose.

### Why the controls look like this, what they cost, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Degrade, do not stop. The breaker makes answers cheaper and a little worse, and the service stays up. A budget that stopped DocuMind would turn a finance question into an outage.

- A replay instead of a spend. `SPEND_PCT` shows what the lane does at any spend without spending anything, on a candidate that takes no traffic.

- The API keeps its own counter. `tenant_daily` answers a day late, so the breaker reads a Firestore document that every answer adds to (`budget.py`'s docstring).

- Floors are explicit, and end the day at zero. `off.tf` puts it in rupees: a forgotten L4 costs an evening, at Rs 121 an hour, not a month, at Rs 86,904.

- A quota under `max-instances`. `max-instances` is one service's limit and the quota is the project's, so one typo cannot double the GPU bill (`gpu_quota.py`'s docstring).

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The breaker's 100 percent action is only a comment. `breakers.py` says min-instances 0 at 100 percent and declares `BUDGET_FLOOR_PCT = 100`, and nothing in the kit reads it. Past 100 percent the lane routes exactly as it does at 80.

- `make candidate` cannot replay a spend. It carries `ROUTING` but not `SPEND_PCT` or `BUDGET_USD`, which is why step 5 uses `gcloud`. Because environment variables carry over, a replay left on the template rides into the next revision.

- The router's per-tier settings never apply. `router.py`'s `ROUTING_TABLE` gives each tier a thinking budget and an output cap (COMPLEX: 8,192 and 16,384). The request path imports only `classify()`, and the generator answers every tier with thinking `LOW` and `max_answer_tokens` 2,048.

- The classifier's call is priced nowhere, and the class is recorded nowhere. The usage row carries the answer's tokens and the model. A routed question's flash-lite call is on no row, and neither is its class.

- The two budgets never meet. The breaker reads model spend in dollars against `BUDGET_USD`, and the billing budget reads the whole bill in the account's currency against `BUDGET_AMOUNT`. The billing budget acts on nothing. Its Pub/Sub topic is off by default (`budget_pubsub`), and when declared, nothing in the kit reads it.

- The off switch knows four services. `documind-mcp` and `documind-agent` also take `MIN_INSTANCES` (`lesson-7.2.sh`, `lesson-8.4.sh`), and neither the 23:00 job nor `make off` floors them.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Here is what this lesson left on your lane:

- A candidate revision was made, routed six questions (one to Pro), and was undone. The live revision never moved.

- The counter grew by those six answers' costs.

- The UI's floor went to one and back to zero.

- The L4 quota in `us-central1` is capped at one card; `make gpu-cap-off` removes the override.

Lesson 11.7 reproduces the agent failures production shows and no eval row does, each with a drill that restores itself.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.6 Exercise model routing, budgets and shutdown controls · v5.0

Next: Lesson 11.7 Reproduce the agent failures production shows and no eval row does.
