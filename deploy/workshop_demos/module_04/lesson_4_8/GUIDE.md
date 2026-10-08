# Lesson 4.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_4.8_DLP_Guard_Audit_WIX.html`, reviewed at blob `b60e0c11b63c21fda4508d9185902d1106f5f2ee`. Learners read that page on the course site; this guide keeps its prose.

Lessons 4.6 and 4.7 settled who may ask. This lesson is about what may be read, what may be said, and what is written down. You upload a note carrying the kit's synthetic PAN, GSTIN, Aadhaar and mobile, and find each one recorded by type, never by value. You switch Model Armor on for a candidate revision and send it a plain question, an injection in English, the same injection in Hinglish and a question about a PAN. Then you read the audit events the upload left in a bucket that refuses to delete them, and you check what the admin console's audit tab can and cannot show.

- Three controls: a scan before indexing, a guard on both sides of the model, a record nobody edits

- The words: info type, finding, template, MATCH_FOUND, ARMOR, audit event, retention and lock

- Before you run anything: set up the shell

- The PII scan: one list, and a note that trips it

- The findings: types and offsets, in Firestore and in the DLP tab

- Model Armor: the template, the guard, and a candidate with ARMOR=on

- Four questions to the candidate: plain, two injections, a PAN

- The audit trail: the events in the retention bucket

- The audit tab: what the admin console reads, and what it misses

- Why the controls are shaped this way, what they cost, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn why the PII scan runs before indexing and never quotes what it found, why Model Armor screens the question before retrieval and the answer only once it is complete, and why an audit event goes to a bucket rather than a table. Then you will prove each control on your lane: the PAN in the findings and in the DLP tab, a 400 `prompt_blocked` from the candidate, and the upload's own events in the audit bucket. You will also see that the admin console's audit tab does not show that upload, and why.

### Three controls: a scan before indexing, a guard on both sides of the model, a record nobody edits

Each control sits at the one point where it can still stop what it exists to stop.

The PII scan runs before indexing, because after indexing it is too late. Once a chunk is embedded and upserted, any question can retrieve it. A scan run afterwards only describes a leak that has already happened. So the ingest worker sends every chunk of a document to Sensitive Data Protection (DLP) before anything is written. It uses one list of 7 info types, Indian identifiers first, and counts a match only at `LIKELY` or above. A finding records the type, the likelihood and a byte offset, never the matched text: a findings store that quoted each PAN would become the place PANs are kept. If DLP cannot be reached, the whole message fails and is retried. An unscanned document never reaches the index.

Scanning records PII; it does not remove it. A document with findings is still indexed, because a vendor contract with a GSTIN in it is exactly what the tenant uploaded it to search. The findings tell the operator where PII sits, the admin console's DLP tab draws them, and lesson 4.7's tenant walls decide who may retrieve it.

Model Armor screens both sides of the model. The question is screened before retrieval. An injection that reaches the retriever has already chosen which documents the model will read, and no filter on the answer can undo that choice. A blocked question is a 400 with the reason, `prompt_blocked`, and costs no retrieval and no model call. The answer is screened after the model finishes, on the complete text. A guard that watched tokens as they streamed past would already have shown the user half of what it meant to block. So when the guard is on, the streaming endpoint holds its tokens until the whole answer has been screened. A blocked answer is a 502 with `response_blocked`. The guard is a switch, `ARMOR`, and it is off by default. This lesson turns it on for a candidate revision that serves no traffic.

The audit trail is a set of files nobody can change. Each event is one JSON object, written once to a Cloud Storage bucket whose retention policy refuses to delete or overwrite an object for five years. The action must be on a registered list, and the writer refuses to drop an event it cannot store. The ingest worker writes `doc.upload` and `dlp.finding`. The admin console writes its own events there too, and also copies them into a Firestore index, `audit_index`. That index is what its audit tab reads, so events that only the worker writes never appear in the tab.

A bank branch's back office. Every form that arrives is read before it is filed, and a clerk writes in the register: PAN on page 2, Aadhaar on page 3, never the numbers themselves. If that clerk is away, the form waits in the tray; it is never filed unread. At the counter, a guard listens to what the customer asks and to what the teller hands back, and can stop either. Every filing is also written into a bound, page-numbered ledger kept in the strongroom for five years. The manager keeps a quick-look binder too, but only the manager's own actions are copied into it. A filing done by the back office is in the strongroom ledger and not in the binder.

#### Two pipelines, three controls

Choose a question's path through the guard, or a document's path through the scan. The query side runs exactly as `/v1/query` calls the guard. The upload side follows the worker from the scan to its last audit event, and shows where each record appears.

The query side ports `screen_prompt()` and `screen_response()` from `services/rag-api/main.py`. For all 8 combinations of its choices, the build ran the kit's own two functions with a stand-in guard, and the panel had to agree with each. The upload side follows `services/ingest/main.py`, and the build checks the lines it depends on.

It shows what the code does with a verdict, not what Model Armor or DLP will decide about a given text. That depends on Google's classifiers and on the template's confidence floor, which is why steps 3 and 6 send real text to your lane.

### The words: info type, finding, template, MATCH_FOUND, ARMOR, audit event, retention and lock

Twelve rows, each with the value it takes on your lane.

One distinction to hold: DLP and Model Armor answer different questions. DLP reads documents once, on the way in, and asks what personal data they hold. Model Armor reads every question and every answer, on the way through, and asks whether the text is an attack or unsafe. Its sensitive-data filter overlaps with DLP's job, but step 6 shows it is not the same list.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. Step 3 uploads one small note to acme, and step 8 withdraws it. Step 5 creates a candidate revision that serves no traffic, and step 6 removes its tag. Everything else only reads.

### The PII scan: one list, and a note that trips it

The list both scanners import, the worker's scan, and one upload that must produce findings.

#### Definition

The worker scans a document's chunks in as few DLP requests as their bytes allow: up to 400 KB each, inside DLP's half-megabyte limit. One request per chunk was refused on the first live corpus load for exceeding the requests-per-minute quota. It maps each finding back to its chunk by byte offset and adds the chunk's id. Only then, if there were findings, does it write one record to `dlp_findings` and a `dlp.finding` audit event. After that come embedding, indexing and the `doc.upload` event. The note below carries the four synthetic identifiers from the kit's `evals/README.md`, which are valid in format so DLP fires on them and invented so nothing real is ever on a screen. It also carries an invented name. Its last line records the time to the second, so each run uploads new bytes. The worker recognises bytes it has already indexed by their hash: it acks them as `ingest_already_current` without scanning again, or as `ingest_withdrawn` after step 8. Either way `make ingest-one` would wait five minutes for a line that never comes.

#### The code

#### Do it

The upload fired the worker. The note is text, so it was parsed without Document AI: one page, one chunk. That chunk went to DLP in Mumbai before it was embedded or written to any index. The matches became one record in `dlp_findings` and one `dlp.finding` event in the audit bucket. Then the chunk was embedded and indexed, and `doc.upload` recorded the upload with `"pii": true` in its meta. `>> indexed` is the worker's `ingest_ok`: the note is now searchable in acme, PAN and all. The scan records PII; it does not remove it.

### The findings: types and offsets, in Firestore and in the DLP tab

The records the scan wrote, then the admin console's tab that draws them.

#### Definition

The cell reads the newest 50 records of `dlp_findings`, keeps acme's, and names each document from the ingestion ledger, `sources`. It filters by tenant in Python, not in the query, because Firestore would need a composite index for the ordering and the filter together. For each record it prints the count and the types, then one finding in full, so you can see exactly what is stored and what is not. The admin console's DLP tab reads the same collection and draws the findings as a histogram by type.

#### Do it: the records

#### Do it: the DLP tab

The console sits behind IAP and admits only the addresses the lane was deployed with as `ADMIN_EMAILS`. If it answers `403 - Admins only`, your address is not among them; the cell above has already read the records the tab draws.

The note's record lists five types, and the invoice already in acme's corpus lists its PAN, GSTIN, mobile and email: that invoice's PAN is the one the course plan asks you to find in the DLP tab. The finding printed in full is the whole of what is kept: a type, a likelihood, a byte offset and a chunk id. The PAN itself is in the chunk it was found in, and nowhere else. In the tab, `INDIA_PAN_INDIVIDUAL` has its own bar. The metric above the chart says "Chunks with findings", but it counts records, and the worker writes one record per document.

### Model Armor: the template, the guard, and a candidate with ARMOR=on

What the template filters, where the API calls it, and a revision that calls it.

#### Definition

Terraform creates one template, `documind-guard`, in asia-south1, because it reads prompts that India-resident tenants write. Prompt-injection and jailbreak detection runs at `MEDIUM_AND_ABOVE`. The template's own comment explains why: the polite, code-mixed attempt this market actually sees scores MEDIUM, and a HIGH floor would pass it. Sensitive data runs on the basic configuration, and four responsible-AI filters run at the same floor. The guard blocks when any filter reports `MATCH_FOUND`. In the API, `screen_prompt()` runs after the membership check and before retrieval, so an outsider's question never costs a Model Armor call. `screen_response()` runs on the finished answer. The usage row records its verdict, and a block is raised only after that row is logged, so a refused answer's model cost is still counted. `make candidate ARMOR=on` deploys a revision with the switch on, tagged `candidate` and serving no traffic. Every other setting takes the Makefile's default, which is fine here: the test is only what the guard refuses.

#### The code

#### Do it

Cloud Run built a new revision of `documind-api` with `ARMOR=on` and gave it its own address, `candidate---`, while every other request still reaches the live revision. The target recorded the revision's name in `.candidate-revision`, the file `make promote` reads. Step 6 deletes it, so nothing can promote a guard test by accident. The candidate accepts the same token as the live service, because the API checks every token against its canonical URL.

### Four questions to the candidate: plain, two injections, a PAN

Each status beside the first characters of its body, then the candidate's tag removed.

The cell asks acme four questions as you. The plain question must be answered. The English injection is a textbook attempt, and it must come back 400 `prompt_blocked`. The Hinglish one asks for the same thing the way people here actually type it, and it is the reason the template's floor is MEDIUM. The last question contains a synthetic PAN, and it tests the template's sensitive-data filter.

The plain question went through both screens and was answered. The two injections were refused before retrieval: no chunk was read, no model was called, and the API's log has one `guard` line for each, with `blocked_prompt` and no usage row. That 400 is this lesson's second proof. If the Hinglish line comes back 200 on your lane, the classifier scored it below MEDIUM, and that is worth writing down: it is exactly the failure the template's comment warns about. A 500 on the plain question means the guard itself failed, for example a missing `roles/modelarmor.user`, and the revision's log names the error. On a guarded revision, that means every question fails.

The template's comment says its sensitive-data filter applies "the same India info types the ingest worker scans with". Google's Model Armor overview lists the basic configuration's types as credit card numbers, US Social Security and taxpayer numbers, financial account numbers, and Google Cloud credentials and API keys: no PAN, Aadhaar or GSTIN. So expect the PAN question to be answered, and read what the answer says. If it names the invoice's PAN, Model Armor let an Indian identifier through on the way out as well as on the way in. Screening Indian identifiers here takes the advanced configuration, which points at a DLP inspect template naming the same 7 types as `shared/pii.py`.

#### Clean up: the candidate's tag

Removing the tag takes the candidate's address away; the revision itself stays in the service's list, with no traffic. The service's configuration still says `ARMOR=on` until the next deploy or candidate sets it: `make up` and `make candidate` both pass `ARMOR`, and both default it to `off`.

### The audit trail: the events in the retention bucket

The writer every service shares, the bucket that keeps what it writes, and the two events your upload left.

#### Definition

`emit()` checks the action against the 23 registered names, builds one event and uploads it as one object. The path starts with the day and the actor's tenant, so one tenant's day is one prefix to list. The bucket's retention policy is five years. Until an object is that old, Cloud Storage refuses to delete or overwrite it, for the project's owner as much as anyone else. Locking is a separate decision. A locked policy can never be shortened or removed, and Google puts a lien on the project, so neither the bucket nor the project can be deleted until the last object ages out. That is why the lab leaves the policy unlocked unless you deploy with `AUDIT_LOCK=true`. The worker holds only `roles/storage.objectCreator` on the bucket: it can add an object and nothing else. The cell lists today's acme objects, prints the newest `dlp.finding` event field by field, reads the retention settings, and then tries to delete that event. The delete must be refused. The cell attempts it only when the bucket reports a retention period.

#### The code

#### Do it

One upload left two events under today's acme prefix, `dlp.finding` and `doc.upload`, and this is the third proof: the upload, recorded where nobody can remove it. Both events name `system:ingest` as the actor, because the worker sees an object in a bucket, not the person who put it there. Cloud Storage's own Data Access audit logs can record who wrote the object, if they are enabled. The event's meta carries the types and a count, never the values, the same rule the findings follow. The retention line is the kit's five years, and the refused delete is that policy at work.

### The audit tab: what the admin console reads, and what it misses

The console's copy of its own events, the tab that lists it, and the note withdrawn.

#### Definition

The admin console's `emit()` calls the same shared writer, then copies the event into `audit_index` in Firestore. Its audit tab lists that collection, newest first, up to 500 rows. Listing a bucket prefix for every page view would be slow, and the index is the console's answer to that. But nothing else writes the index. Across the whole kit, only the console's own `emit()` does, and the only event the console emits today is `tenant.create`. The worker's `doc.upload` and `dlp.finding`, and the MCP server's `query.submit`, go to the bucket alone. The cell counts the index's actions.

#### The code

#### Do it

`doc.upload in it: 0`: the tab cannot show the upload you made in step 3, although step 7 found it in the bucket. The course plan asks for "the upload in the audit tab", and on the kit as it stands that proof cannot be met. The event exists, in the record that counts; the page that should show it reads a different store. Either change would close the gap: the worker writes the index as well as the bucket (its account can already write Firestore), or the tab lists the bucket's day-and-tenant prefix, the same read step 7's cell makes. The tab's action list also offers `doc.upload`, `doc.delete` and three other actions that nothing writes to the index. It offers neither `dlp.finding` nor `tenant.create`, the one action the index does hold.

#### Clean up: withdraw the note

The note came from you, and it should not stay in acme's corpus. `make retire` flags its chunks, which leave retrieval, and marks its ledger row `WITHDRAWN`; the object stays in the uploads bucket. Look at what stays. The findings record stays in `dlp_findings` until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: `doc.delete` is a registered action, and nothing in the kit emits it.

### Why the controls are shaped this way, what they cost, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- One list, in one file. `shared/pii.py` exists because two lists drift. Then the scan misses a type, the dashboard reports zero findings, and both are working correctly. The admin console's `dlp.py` imports the list and never defines its own.

- No quotes, anywhere. `include_quote` is false in the scan. The template turns on `log_sanitize_operations`, and its comment gives the rule: log what was sanitised, never the text. A findings log that quotes a PAN has moved the PAN somewhere harder to delete than the document.

- A failed scan is a failed ingest. DLP's own retries cover a rate-limit refusal for about five minutes. After that the message is nacked and redelivered, and after 12 delivery attempts Pub/Sub moves it to the dead-letter topic, where a person decides. Indexing an unscanned document is the exact thing the control exists to prevent.

- Pictures are scanned too, elsewhere. A figure's bytes are scanned before its caption is indexed, because a caption of an invoice can carry the invoice's PAN. DLP inspects images only in a short list of locations, and asia-south1 is not on it, so the pixels go to Singapore while the text stays in Mumbai. `DLP_IMAGE_LOCATION` overrides that.

- A block is a status code, not a polite answer. A refusal written to look like an answer would hide how often the guard fires. A 400 and a 502 are counted by every dashboard that counts errors.

- The guard fails closed. Without `roles/modelarmor.user`, the first sanitize call fails, and so does every question. That is why the role is granted whether the switch is on or off: the role costs nothing while the switch is off.

- The writer refuses to drop an event. With `AUDIT_BUCKET` unset, `emit()` raises instead of skipping the event, and the worker checks for the variable at startup rather than on its first document. The MCP server is the one exception, on purpose: it logs a failed audit write and still answers.

#### What it costs

Each point below is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The audit tab never shows a worker event. Only the admin console writes `audit_index`, as step 8 showed.

- The template's sensitive-data filter does not know Indian identifiers. Its comment says it does; the basic configuration's list, on Google's page, does not include them. Step 6's fourth line is the test.

- Nothing expires `audit_index`. The console's docstring and caption promise 14 days, and no TTL policy in `terraform/` names the collection. The tab's action filter also needs a composite index on action and time, and `firestore_indexes.tf` defines none. Until one exists, Firestore refuses that query and asks for the index.

- The DLP tab's metric says "Chunks with findings" and counts documents. The label dates from `inspect_and_log()`, which wrote one record per chunk; nothing calls it now.

- A withdrawal is not audited. `doc.delete` is registered, the tab offers it, and nothing emits it.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

The note was indexed in acme in step 3 and withdrawn in step 8. Its object stays in the uploads bucket, and its ledger row says `WITHDRAWN`. It also leaves permanent traces: one record in `dlp_findings`, and two audit events that the bucket will keep for five years. `documind-api` has one more revision, which serves no traffic and has no tag. The service's configuration says `ARMOR=on` until the next deploy sets it back, and `.candidate-revision` is gone. The usage rows of two answered questions, and two guard lines in the API's log. No roster, role, policy or setting changed. Lesson 4.9 reads the failures first, then attacks your own pipeline with a held-out set built on this lesson's four probes.

Netsetos GenAI on GCP · Module 4 Evals and safety · Lesson 4.8 Exercise DLP, guardrails and audit behavior · v5.0

Next: Lesson 4.9 Read the failures first, then attack your own pipeline.
