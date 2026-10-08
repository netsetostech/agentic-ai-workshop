# Lesson 11.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_11.5_Usage_Reconcile_WIX.html`, reviewed at blob `f7064bb5d693cc1baf873d3389be6b6a2b2e3ab5`. Learners read that page on the course site; this guide keeps its prose.

Every answer DocuMind gives writes one usage row: the tenant, the tokens, the cost priced at the model that answered, and where the time went. Four readers count those rows, each with its own filter and its own window. Cloud Logging keeps them all. A log sink copies some of them into BigQuery, where the `tenant_daily` view groups them by Indian day. `make usage` reads them straight from the log. A log-based metric counts them for an alert.

When two readers disagree, the difference points to a filter or a window. In this lesson you ask four questions and reconcile the view's rupees with `make usage`'s, group by group, to the paisa. Then you read the lane's alert policies and find that none of them watches the dead-letter queue. You add the one that should, and trip it.

- One row, four readers

- The words: usage row, sink, view, reconcile, metric, policy, incident

- Before you run anything: set up the shell

- The readers, as the kit writes them down

- Four questions, four rows

- Reconcile the view with make usage

- The alert the dead-letter queue never had

- Why the readers differ, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn which reader counts which row, and why two honest reports can disagree without either being wrong. Then you will prove two things on your lane:

- `tenant_daily`'s rupees equal `make usage`'s for the same day, group by group;

- a message in the dead-letter queue opens an incident.

### One row, four readers

Each reader has its own filter and its own window, and the differences are where reconciling starts.

One row per answer. Each surface writes its own row:

- `usage_row()` in `main.py` builds the row for `/v1/query` (event `query`) and for `/v1/stream` (event `stream`).

- Media Studio writes its own row with the same fields (event `media`).

- The chat service writes a row per turn (event `chat`) with the brain, the tool calls and the latency, and, since lesson 5.5, the turn's own model calls with their tokens and cost.

Each row is a line on the service's standard output, which Cloud Run turns into a Cloud Logging entry.

Four readers count the rows.

- Cloud Logging keeps every entry for thirty days.

- The sink, `documind-api-to-bq`, copies entries into BigQuery as they are written. It copies only from `documind-api` and `documind-chat`, and only the events `query`, `stream` and `chat`, and the four the Desk added: `desk`, `passages`, `desk_shadow` (never a sensitive one) and `desk_gate` (from `documind-chat` only).

- `tenant_daily` groups the sink's table by Indian day and seven dimensions, reading `query`, `stream` and `media`.

- `make usage` reads the log itself. It reads `documind-api` only, the events `query`, `stream` and `media`, over the last N hours, and at most 2,000 rows.

- `documind/queries`, a log-based metric, counts `query` and `stream` rows as they are written. The unanswerable-rate alert divides by it.

Reconcile the additive measures exactly. Answers, refusals, tokens and rupees add up across rows, so two readers of the same rows must agree to the paisa. Percentiles do not add up, and the two reports compute them differently: the view uses BigQuery's approximate quantiles, and the tool takes the nearest rank. So p95 is compared by eye, not for equality.

Every difference has a cause. The kit builds in three:

- A window. The view counts an Indian day, while `make usage` counts the last N hours, which can cross midnight.

- A filter. Media rows reach `make usage` but never BigQuery, because the sink does not copy them.

- A service. Chat turn rows are copied into BigQuery, then read by neither report.

An alert is a reader too. A log-based metric turns rows into a count. A policy watches a count and opens an incident when it stays over a line long enough. A channel carries the incident to a person. An alert nobody declared reads nothing.

The dead-letter queue is where Pub/Sub puts an upload the worker refused twelve times, and it had exactly that problem: `quota.tf` listed a `dlq_depth` alert, and no resource declared it.

A bank reconciliation statement. Every Indian commerce student has drawn one up. The cash book and the bank passbook record the same transactions, and at month end they disagree. You do not adjust one total until it matches. Instead you list each difference with its cause:

- a cheque issued but not yet presented (a window);

- bank charges the cash book never recorded (a filter on one side);

- a deposit entered twice (an error).

When the list explains the whole gap, the books are reconciled. The bank's SMS alerts are its alert policies. They fire for the transactions they are set up for, and a kind of transaction with no alert sends no message, however large it is.

#### Which reader counts this row?

Tick the rows that happened today. For each reader the panel shows how many rows it counts and their rupees. When `tenant_daily` and `make usage` disagree, it lists the rows that make the difference, and why.

The 8 rows are the kit's own: two from the build's run of rag-api's `query()`, two more from its `usage_row()`, one from `media.py`'s `_usage()` (Rs 3.32 for an image), and one in the chat service's own turn-row shape. Each reader's verdict comes from the filters in `sink.tf`, `tenant_daily.sql`, `usage_rows.py` and `alerts.tf`, parsed at build time.

It applies the kit's filters to eight rows. Your lane's rows, times and rupees are your own, and step 5 reconciles them.

### The words: usage row, sink, view, reconcile, metric, policy, incident

Ten rows, each with the value it takes on your lane.

One distinction to hold: a report can be right about what it reads and still leave out what it does not read. Reconciling finds the rows one reader leaves out; it does not make either report wrong.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `ME` set, and `bq` (Cloud Shell has it).

- The kit at this lesson's version. `grep -c 'alert_policy" "dlq_depth"' terraform/alerts.tf` prints `1`.

- Terraform's state, for step 6's plan. Run it in the checkout where `make up` ran, with the flags you gave `make up`.

- The drill puts one labelled message in the dead-letter queue, and then removes it.

### The readers, as the kit writes them down

Which services and events each one reads, over what window, and the one policy that reads the dead-letter queue.

#### Definition

The cell reads the four readers' files and prints each reader's filter:

- `sink.tf`'s filter, with the two events it copies only on a condition;

- `tenant_daily.sql`'s WHERE and GROUP BY;

- `usage_rows.py`'s `gcloud` filter and its limits;

- the `documind/queries` metric in `alerts.tf`.

Then it lists, for each event, the readers that read it, and the event the Desk's own view, `desk_daily.sql`, reads; the policies `alerts.tf` declares, and those the Desk keeps in `desk_alerts.tf`; and the one that reads `ingest-dlq-sub`. Nothing is called.

#### The code

#### Do it

- `query` and `stream` rows are read by all four readers. On a day with only those, the reports can agree exactly.

- `media` is read by the view and by `make usage`, but the sink never copies it. The view's WHERE names a row that never arrives.

- `chat` is copied by the sink and read by nothing after it.

- The Desk's four events are copied too, and none of the other three readers reads them. A sensitive `desk_shadow` row and rag-api's `desk_gate` rows stay in Cloud Logging: each can sit beside a `chat` row of the same turn, which names the person. The Desk's own view, `desk_daily`, reads `desk` (lesson 10.4).

Both rupee columns use 85 rupees to the dollar. The Desk's policies sit in their own file, the router's three only on a lane planned with `DESK_ROUTER_ALERTS=true` and the gate check's failed share only with `DESK_GATE_ALERTS=true`, so `alerts.tf`'s list is the one this lesson counts. The last line is this lesson's kit change: `alerts.tf` now declares a policy on `ingest-dlq-sub` (its excerpt is in step 6). Your lane gets it only when you apply it.

### Four questions, four rows

Three for acme and one for zeta, answered by the live revision, then `make usage` over the last hour.

#### Definition

The cell asks four golden questions as `documind-ui-sa`:

- lk-01 and lk-06, for acme;

- rf-01, for acme, which the corpus cannot answer;

- iso-01, for zeta.

Each answer writes one usage row. The cell prints what the answer itself carries: answered or refused, tokens in and out, and `cost_usd`. Then `make usage` groups the last hour's rows five ways (by tenant, model and backend, brain, surface, and retrieval store) and shows where the time went.

#### Do it

`cost_usd` is `None` on all four answers: a Vertex answer carries its tokens but not its price. The price is worked out when the row is written, by `usage_row()` from `cost.py`'s rates, and it exists only on the row.

`make usage` shows the price:

- acme's three answers, one of them the refusal. A refusal still costs tokens, so rf-01's row counts in the rupees and in acme's unanswerable rate of 0.33;

- zeta's one answer, served by `firestore`. zeta has no pin, so the lane's default store answered it.

If you asked other questions in the last hour, they are in these tables too.

### Reconcile the view with make usage

The same Indian day, grouped the view's way by `make usage`'s own code, compared group by group.

#### Definition

The sink copies each row into BigQuery within a minute or two, and `tenant_daily` reads it from there. The cell:

- reads today's rows from Cloud Logging, from 00:00 IST, with `make usage`'s own filter;

- groups them with `usage_rows.group()` on the view's seven keys;

- asks BigQuery for `tenant_daily`'s rows for today, `CURRENT_DATE('Asia/Kolkata')`;

- compares each group: answers, refusals, tokens in and out, and rupees;

- prints, per tenant, the rupees each side adds up to, and any media rows, which only `make usage` counts.

If `bq` says `tenant_daily` does not exist, run `make bq-views` once. It needs one answer on the lane first, and step 4 gave it four.

#### Do it

Today has two groups, acme through the index and zeta through Firestore, and both are equal in every additive column. The rupees match to the paisa because both sides round the same sum the same way: the view with `ROUND(SUM(cost_usd) * 85, 2)`, the tool with `round(usd * 85, 2)`.

That is the first proof: `tenant_daily`'s rupees equal `make usage`'s for the same day.

The window is what made it exact. Two other runs could differ, and each difference would be a cause, not an error:

- `make usage HOURS=24` may include yesterday evening's rows, which the view files under yesterday;

- a Media Studio image would appear in `make usage` and never in the view.

### The alert the dead-letter queue never had

What pages you today, the policy that should, planned and applied through the kit, and a drill that trips it.

#### Definition

The first cell reads your lane's alerting. It lists the log-based metrics, then each alert policy through the Monitoring API, with the metric and the service or subscription it watches. It ends on the question this lesson asks: does anything read `ingest-dlq-sub`?

#### Do it: what pages you today

A lane made up before this kit version has 5 policies. They watch latency, the unanswerable rate, failed ingests, and two GPU services left warm. None watches the dead-letter queue. An upload the worker refuses twelve times lands there, and nobody knows until someone runs `make dlq`.

#### The policy

The policy watches `num_undelivered_messages` on `ingest-dlq-sub`, a gauge Pub/Sub samples once a minute. Above zero for a minute opens an incident, which goes to the same channels as every other policy: your admins' email, and PagerDuty when a key is set.

It is applied the kit's reviewed way:

- `make plan` writes a saved plan, and refuses any plan that deletes or replaces something. So pass the flags you gave `make up`: `ADMIN_EMAILS`, and `RECONCILE_JOB=true` if you declared the nightly job.

- The first line of `make up` then applies exactly that plan, without the builds and deploys the rest of `make up` runs.

#### Do it: plan and apply

One to add, nothing to change, nothing to destroy.

- If your plan lists more, your lane is behind the kit. Read each addition before applying, or run `make up` as the kit intends.

- If `make plan` stops with `Plan blocked`, a flag differs from the one your `make up` used. Fix the flag, never the check.

#### Do it: the drill

A drill proves the alert end to end without waiting an hour for a poison upload. The cell publishes one message straight to the dead-letter topic, labelled `drill=13.2`. After five minutes it reads the gauge the policy reads, a sample a minute, and the policy itself.

The gauge went from 0 to 1 when the message landed, and stayed above zero. The condition holds, so the policy opened an incident:

- in the console, Monitoring > Alerting lists it as open, under `Ingest dead-letter queue holds messages`;

- the email goes to the addresses in your `ALERT_EMAILS`.

That is the second proof: an alert tripped by the dead-letter queue. `make poison` takes the real path to the same incident: a zero-byte upload, refused twelve times over about an hour, then the dead-letter queue.

#### Do it: drain the drill message

The drill message must not stay in the queue, and a real message must not be thrown away with it. The cell pulls without acknowledging, acknowledges only the messages labelled `drill=13.2`, and leaves anything else for `make dlq`.

One message pulled, one acknowledged. Once the next samples read zero, the condition stops holding and the incident closes.

### Why the readers differ, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- One row shape. `usage_row()`'s own docstring calls it the one shape every observability consumer reads. `tenant_daily`, `make usage` and the metrics read the same fields, which is what makes reconciling possible at all.

- Two stores, two jobs. Cloud Logging has the rows the moment they are written, for thirty days: that is `make usage`'s store. BigQuery keeps a queryable copy for months: that is the view's store.

- Money adds up, and percentiles do not. Reconcile answers, refusals, tokens and rupees exactly, and read the latency quantiles side by side.

- Alerts follow failures the course has met. Each policy names one, including this lesson's: the dead-letter queue nobody read.

- A drill tests the whole chain. The gauge, the policy, the incident and the channel, without waiting for a real failure.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- Media rows never reach BigQuery. The sink copies `query`, `stream`, `chat` and the Desk's four events, never `media`. `tenant_daily`'s WHERE reads `media`, and its comment promises media spend per tenant, but no media row ever arrives. `make usage` counts them, so a day with images disagrees by exactly their rupees.

- A chat turn's own model calls are in no report. The chat service's turn row prices them, in `cost_usd`, but neither report reads that row. The retrievals the brains make are counted, on rag-api's rows labelled with the brain; the agent's own Gemini calls are not. Lesson 11.6 takes this up.

- The answer does not carry its price. A Vertex answer's `cost_usd` is `None`. Only the row is priced, so a caller cannot see what an answer cost.

- The admin console shows no rupees. Its Cost tab is still a stub that points to a lesson of the notebook course. Its Usage tab's "p95 latency" is the median of the view's p95 rows, not a p95 of the answers.

- The sink's table has a table lifetime, not a partition lifetime. The dataset sets `default_table_expiration_ms` (90 days) and no `default_partition_expiration_ms`. BigQuery gives a new table the table lifetime, so the table the sink creates is set to expire whole, 90 days after it was made, rather than day by day. Check yours: `bq show --format=prettyjson "$PROJECT:documind_observability.run_googleapis_com_stdout" | grep -i expiration`.

- Three of `quota.tf`'s alerts are still intents. Its map lists 5 alerts, and `alerts.tf` declares two: `unanswerable_rate`, and `dlq_depth` since this lesson. `guardrail_blocks`, `cache_hit_low` and `burn_rate` are declared by nothing.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Four questions were asked, three for acme and one for zeta, and their rows are in Cloud Logging and in `tenant_daily`. The dead-letter policy from `alerts.tf` is now on your lane, and will page your admins the next time an upload reaches the dead-letter queue. The drill message was acknowledged, and the incident closed. Lesson 11.6 exercises the controls those rupees feed: model routing, the budget and the shutdown.

Netsetos GenAI on GCP · Module 11 Project · Lesson 11.5 Reconcile usage events, reports and alerts · v5.0

Next: Lesson 11.6 Exercise model routing, budgets and shutdown controls.
