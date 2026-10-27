# Lesson 8.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_8.1_PubSub_Kafka_WIX.html`, reviewed at blob `1e9a96b64334dbc3d0d7d57f73ef634d3ecaaa83`. Learners read that page on the course site; this guide keeps its prose.

Lesson 1.4 followed a document to its records and lesson 1.5 followed a message through its retries. This lesson follows the bus between them as a part you could replace. One upload is traced from the object's generation through the notice, the push and the acknowledgement to the records and an answer that cites it. The subscription's settings are read off the platform: the five the kit declares and the five it leaves to Google. The kit's thirty-one corpus objects are pushed at a worker squeezed from thirty instances to five. And every setting is set beside its Kafka counterpart, with the gap between them.

The point of the mapping is not that one bus is better. Each choice in the kit, from the claim on the content hash to the versioned bucket, is what makes a forgetful bus enough, and by the end you should be able to say which of them a move to Kafka would make you rebuild.

- What an event bus does, and the two shapes it comes in

- The words: topic, subscription, push, ack, retention, offset, partition, consumer group

- Before you run anything: set up the shell

- The UI: one note in, its row, and an answer that cites it

- The kit's code: what the subscription declares, and what it leaves to Google

- REST: the trace hop by hop, and the subscription as Pub/Sub holds it

- Direct reads: the records the push left, and the answer through the API

- The burst: thirty-one objects against five instances

- Pub/Sub mapped to Kafka: thirteen rows, and when Kafka would be the better bus

- Verify it yourself: the checklist

You will learn what the kit's Pub/Sub path declares and what it leaves to Google's defaults, follow one upload of your own from the object's generation to the push, the acknowledgement, the records and a cited answer, squeeze the worker to five instances while the corpus lands, and set each setting beside its Kafka counterpart.

### What an event bus does, and the two shapes it comes in

A notice that something happened, carried from the code that saw it to the code that must act: either as a queue that forgets what is done, or as a log that keeps everything.

The bus carries a notice, not the document. When an upload lands in DocuMind's bucket, the worker has to index it, and the two never call each other. Cloud Storage publishes a notice, about a kilobyte of the object's metadata, into a Pub/Sub topic. A subscription on that topic remembers the notice until someone has dealt with it, and pushes it to the worker as an HTTP request. The document's bytes never travel on the bus. They stay in the bucket, which keeps every version, and the notice names the version: the object's generation. The worker fetches exactly that generation, and every hop of this lesson's trace carries that one number.

Two shapes of bus. A queue tracks each message on its own. Pub/Sub's subscriptions work this way: a message is delivered, and if the reader acknowledges it, it is gone; if the reader refuses it, or stays silent past a deadline, it is delivered again. A log keeps every message, in order and numbered, for a fixed time, whether anyone read it or not. Apache Kafka works this way. Each reader keeps its own position in the log, its offset, and moves it forward when it has done the work. Push and pull follow from the shape: Pub/Sub can push to an endpoint and decide the pace itself, while a Kafka consumer always pulls, at its own pace.

What each shape gives you for free. A queue gives you retries and a dead-letter topic as settings, and it forgets: replaying yesterday's messages needs retention that you have to switch on first. A log gives you replay as a matter of course, since moving an offset back is the whole operation, and leaves retries and dead letters to the code you write. The kit chose the queue, and its other choices are what make the queue enough. A claim on the content hash turns a second delivery into a harmless duplicate. A generation guard turns a late delivery into a harmless stale event. And the versioned bucket is the real record, which the nightly walk replays from by rewriting an object onto itself. Step 8 sets all thirteen differences side by side; step 7 shows the one you can feel, which is what a pushing bus does when its reader is full.

A courier, or the goods shed's register. There are two ways a parcel can reach an office in Bhiwandi. A courier brings each parcel to the door and waits for a signature. Once it is signed for, the courier's company forgets it; if it is refused, the courier comes back later, again and again up to a limit, and then leaves it at a depot. One courier route serves one office. A second office that wants the same parcels needs its own route, and gets only the parcels that arrive after its route begins. That is Pub/Sub: the subscription is the route, the push is the courier, the 200 is the signature and the dead-letter topic is the depot.

The goods shed at the railway station works the other way. Every parcel that arrives is written on the next numbered line of a register, and nobody carries anything anywhere. Each office sends its own clerk, who keeps a bookmark in the register, collects whatever lies past it, and moves the bookmark once the parcels are put away. The register is pulped after a week, read or not, and a new office can start from the first line still there. That is Kafka: the register is a partition, the line number is an offset, the bookmark is a committed offset and the clerks are a consumer group. DocuMind's parcels, though, are slips, not boxes: each names a shelf in a warehouse that keeps every version. That is why the kit can afford a courier that forgets.

#### The trace: one upload, hop by hop, on both buses

The panel follows this lesson's upload through the kit's real path. Pick a hop to read what happens on your lane, the number that bounds it, and what the same hop would be on Kafka. Switch the worker's answer to watch a refusal take the other road, the one lesson 1.5 drills. Every name and number in the panel is read from the kit when this page is built: `eventarc.tf` for the topic, the subscription and its policy, `lesson-12.5.sh` for the worker's limits, `main.py` for what the handler reads and answers, and the worker's own chunker for the note's chunks. The Kafka column is Kafka's general model, not a kit you can run.

Hops 1 to 5 are the same whatever the worker answers; hops 6 to 8 follow its answer. The numbers in each card's lane column come from the kit's files, Google's documented defaults where the kit sets nothing.

Read the two columns down to hop 6 and the difference is plain. On your lane Pub/Sub decides when to deliver, how fast, how often to retry and when to give up, and the worker only answers. On Kafka the consumer decides all four, and the broker only keeps the log. The rest of this page proves the left-hand column on your lane, one hop at a time.

### The words: topic, subscription, push, ack, retention, offset, partition, consumer group

Fourteen terms, Pub/Sub's and Kafka's, each with what it is on your lane.

Two pairs in this table are easy to confuse. A topic is where messages are written and a subscription is where they are read: on Pub/Sub, the state of every message (delivered, acknowledged, how many attempts) lives on the subscription, so two subscriptions on one topic each get their own copy. And an acknowledgement is not a commit: acknowledging deletes one message from one subscription, while committing an offset on Kafka moves a bookmark and deletes nothing.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

### The UI: one note in, its row, and an answer that cites it

The upload this page traces, made once, then seen the way a user sees it: a row under Versions, and an answer with a citation.

The trace needs an upload nobody else could have made, so the cell below writes a short note of your own: a title line, the time you made it, and two invented sections. The time makes its bytes, and so its content hash, new to your lane. Then `make ingest-one` copies it under acme's prefix and waits for the worker's `ingest_ok` line. That is the kit's own drill:

Two lines, and between them the whole bus ran. The object was finalized, Cloud Storage published its notice, Pub/Sub pushed it, and the worker read it, wrote the records and answered 200. The second line is the worker's own `ingest_ok`, read back from Cloud Logging: the version's `doc_key` (acme and the note's SHA-256), 3 chunks and 1 page, since a text file has no page breaks. Keep the name `acme/pubsub_trace_note.md` in mind; every read below uses it.

Now the user's side. Open the UI (`https://documind-ui-NUMBER.asia-south1.run.app`) signed in to Google as yourself, and choose Documents. Under Versions the note has its own row: status `indexed`, `chunks` 3, `reused` 0, `embedded` 3, and the minute it was indexed. If the row is not there, choose Refresh indexing status: the page reads the ledger through the API each time it draws. Then choose Chat and ask the note's question:

After 9 pm, where do couriers deliver at the Bhiwandi depot, and who signs for the parcel?

The answer should name gate 3 and the security desk, with a citation pill. Open Sources under it: one of them quotes the note's NG-01 section, and its button opens the note itself. A document your lane had never seen two minutes ago is now evidence an answer can cite. The UI's own uploader would have taken the same road. Index documents writes the file under your tenant's prefix in the same bucket, so it fires the same notice:

This is also where the two identities from the setup part ways. `make ingest-one` copied the note as you, the operator, with gcloud's sign-in. The Versions table and the chat asked the API as you, the person, through the roster, which maps your email to acme. The bus does not care who wrote the object: an object under `acme/` is acme's, whoever put it there.

### The kit's code: what the subscription declares, and what it leaves to Google

The notice, the subscription, the worker's limits and the handler's first lines, read for their settings: five declared, five left to Google.

Lesson 1.5 read this path for its retry rule. This step reads it for its settings, because the settings are what you would have to reproduce, or give up, on another bus. Three files hold them all.

#### The notice

One rule on the uploads bucket: publish a notice for every `OBJECT_FINALIZE`, in the `JSON_API_V1` format, into `documind-ingest`. Google documents three properties of these notices. They arrive at least once, so one upload can produce two messages with two message ids. They usually arrive within seconds, but with no promise of a time. And they are not promised in order. Google's advice to a reader that acts on a notice is to make the object's generation (with its metageneration) a precondition of the action, and the worker's guard does exactly that with the generation:

An older generation than the ledger's is a late notice and is acknowledged as `stale`; anything else is fetched by its own generation, never as "whatever the object holds now". That one rule is why order does not matter to the kit, and step 8 comes back to it.

#### The subscription

Four settings, each a decision with a reason in its comment or in lesson 1.5. Everything else about the subscription is Google's default. Side by side, from the Terraform above and Google's documentation, read on 12 October 2026:

The defaults are not mistakes. Each fits a lane whose uploads are few, whose one reader keys everything on the content, and whose bucket can replay any object. Two of them deserve a second look all the same. Retention: a notice nobody acknowledges waits 7 days and is then dropped, so a worker broken for longer than that loses its notices, and only the nightly walk of lesson 1.8 would find the objects with no ledger row. Expiration: Google deletes a subscription that has had no subscriber activity for 31 days, and a successful push is the activity, so a lane with no upload for 31 days loses `documind-ingest-push` itself until the next `make plan` and apply recreate it. The same default applies to `ingest-dlq-sub`, which nothing reads unless you run `make dlq`. The kit's other push subscription, the one behind lesson 10.4's Google Chat door, sets both on purpose:

Its comments say the values were written from memory. Google's documentation confirms both: the expiration defaults to 31 days and can be set to never expire, and a retention can be as short as 10 minutes. The same file also keeps that door's messages in India with a storage policy on its topic; `documind-ingest` declares none.

#### The worker that receives

The subscription knows none of these numbers. Pub/Sub learns the worker's capacity only from its answers. 1 request per instance and at most 30 instances make 30 deliveries in flight. A delivery beyond that waits in Cloud Run's pending queue for 10 seconds or 3.5 times the average start-up time, whichever is longer, and if no instance frees up it is refused with a 429, which Pub/Sub counts as a failed delivery like any other (Google's autoscaling page). Step 7 squeezes the 30 to 5 to watch that happen. The 600-second request ceiling is the subscription's 600-second deadline seen from the other side: a request the worker cannot finish in time is a delivery Pub/Sub will make again.

#### The handler, and what it reads of the message

The envelope Pub/Sub posts carries the message's id, its publish time, its attributes (the object's generation among them) and, because the subscription has a dead-letter policy, a count of delivery attempts. The handler reads one field: `message.data`, the object's record, which it parses into `IngestMessage`. Nothing else of the envelope is read anywhere in `main.py`, and that is a decision, recorded on the contract:

A message id names one message; a content hash names what was delivered. The worker keys everything on the second, which is why a duplicate is harmless whichever bus brought it:

One consequence for the trace. The worker's log lines carry the object's generation and the version's key, never a message id or an attempt number, and Cloud Run does not join a container's plain log lines to the request that produced them: Google's logging page says that needs a Cloud Logging client library or a trace field, and the worker writes plain JSON to stdout. So the next step joins the hops by time and by generation, not by an id.

### REST: the trace hop by hop, and the subscription as Pub/Sub holds it

Three Google APIs, read with your operator token: Cloud Storage for the object, Cloud Logging for the push and the worker's lines, Pub/Sub for the subscription and its topic.

The first cell asks Cloud Storage's JSON API for the note's metadata, which is the record the notice carried. Then it asks Cloud Logging for everything `documind-ingest` logged in the ten minutes after the object was created: the request log entry Cloud Run writes for each POST it receives, and the worker's own JSON lines for this version. It prints them as one timeline, in seconds from the object's creation:

Read it hop by hop. The first line is hop 1 and the start of the clock: the generation is the number the notice carried. Hops 2 to 4, the notice, the subscription and the push, leave no line of their own on your lane. Pub/Sub's own metrics count them, which step 7 reads, and the request log entry is where they end: one POST, answered 200, with the latency of the worker's whole job. Inside that latency are hop 5's reading and hop 7's writes: a `mirror_ok` line for each managed store acme's policy allows, the ledger's new fingerprint, and `ingest_ok` with the object's own generation. The 200 that ended the request was hop 6, the acknowledgement. Nothing in the timeline is joined by an id: the generation does the joining, as step 4 said it must. The `ingest_ok` line also becomes two points on the kit's log-based metrics: one on `documind/ingest_events`, labelled with the event and the tenant, and its embedded count, 3, on `documind/ingest_embedded`. Step 7 shows which of the worker's verdicts those metrics leave out.

If the worker's lines are missing, the cell says so and prints the window it searched. Cloud Logging can take a minute to show a line, so run the cell again before you suspect the bus.

#### The subscription, as Pub/Sub holds it

Step 4 read what Terraform declared. The platform holds more: every field Google filled in with a default. The cell reads the subscription and its topic from the Pub/Sub API, then reads `terraform/eventarc.tf` in your clone of the kit and marks each field with who set it:

The five declared fields come back as Terraform wrote them, the push endpoint and the token's account in place of the Terraform names, and the never-expire policy as an empty `expirationPolicy` (a lane applied before 13 October 2026 still reports Google's time to live there, 2,678,400 seconds or 31 days, until its next `make plan` and apply). The five marked Google are the defaults in the table above, as the API reports them: the retention in seconds (604,800 is 7 days), and the switches the API leaves out when they are off. The topic's own retention is absent: once the subscription acknowledges a notice, no copy of it exists anywhere in Pub/Sub. Step 8's Kafka mapping turns on that one fact.

### Direct reads: the records the push left, and the answer through the API

Firestore read directly with your own credentials, then the API's two doors onto the same records: the ledger it serves and the question it answers.

The push ended in writes, and two keys find them all without a search, as lesson 1.4 showed. The ledger row is named after the object, `sources/acme~pubsub_trace_note.md`, and it names the version's key, `doc_key`. The cell reads the ledger row, the claim, the version's chunk rows and acme's ledger summary, and holds each generation against the object's:

Three generations, one number: the object's, the ledger's and the claim's. That equality is the trace's proof that one notice, delivered and acknowledged, produced every record. The chunk rows are the three the worker's chunker cuts from the note by its two rules, a chunk for each `##` section and a preamble for the text above the first heading: `preamble`, `NG-01`, `NG-02`. This page ran the worker's own `_chunk()` on the note when it was built, and it cut the same three.

Last, the API's two doors onto the same records. `GET /v1/sources` is the ledger as the UI's Versions table draws it, asked here as the UI's service account; `POST /v1/query` asks step 3's question again:

The ledger row is the one the cell above read from Firestore, as the API serves it, with the managed stores that hold a copy. The answer cites the note: its chunk id is `acme:` followed by the note's SHA-256 and `#1`, the NG-01 section's position, and `stages` says the pool came from the kit's own index (`vector`), because the setup pinned acme there. That citation is the last hop of the trace, and the reason for the first: for DocuMind, an upload has happened from the moment an answer can cite it. The answer left a record of its own, as every answer does: one usage row on `documind-api`'s log, `event` `query`, with its tokens and its cost, which lesson 4.3 reads.

### The burst: thirty-one objects against five instances

The worker's ceiling cut from thirty to five, the kit's corpus uploaded again, and the bus's response read in the request log and in Pub/Sub's own metrics. Then the ceiling put back.

Why squeeze. A bus that pushes has to learn how fast its reader can go, and it learns only from the answers. Pub/Sub starts a subscription's push window small, widens it with each success and narrows it with each failure (Google's push page). Cloud Run holds a request that finds no free instance in its pending queue and then refuses it with a 429. The subscription counts each refusal as a failed delivery, retries it after the backoff, and charges it against the 12 attempts; the comment in step 4's subscription is the kit's record of a first live load that learned this the hard way. At 30 in flight, 31 messages are 2 rounds of work; at 5 they are at least 7, and they have to queue. Squeezing the ceiling makes the reader the bottleneck, so you can watch the bus adapt to it.

Why the corpus. `make ingest-corpus` uploads the kit's corpus again: by `upload.sh`'s rule, 21 objects for acme, 3 for globex and 7 for zeta, 31 in all. Each upload is a new generation, so each fires a notice, and each notice is pushed until the worker takes it. But the bytes are the ones your lane indexed when it was built, so every claim is already taken: the worker downloads the generation, hashes it, finds the claim and answers 200 `duplicate`. Nothing is parsed, nothing is embedded and no model is called. The burst costs deliveries and nothing else, as long as that "every" holds, and the first cell checks it before anything moves:

The cell applies `upload.sh`'s rule to your clone, hashes every file it would upload, and compares each hash with the ledger row for that object. A file that differs is a version your lane does not hold as current. The burst would index it, at its usual cost, and if its bytes are a version the ledger retired, it would make that old version current again. Lessons 1.6 and 6.3 put the handbook back at their ends, so on a lane that followed them every file matches. If one does not, stop here and find out why before you go on. A clone checked out on Windows with line-ending conversion, for example, turns every Markdown file into new bytes.

#### Squeeze, then upload

The ceiling is a setting of the worker's revision: the same `--max-instances` flag `lesson-12.5.sh` deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed.

Now note the time and upload the corpus. Keep this shell open: the next three cells read `BURST_SINCE`. If the shell does close, export it again with the time this cell printed.

`upload.sh`'s closing lines are older than the kit's path. There is no Eventarc trigger (step 4's notice replaced it), and the pull it suggests would acknowledge, and so delete, whatever the dead-letter subscription holds. Use `make dlq`, which only looks. If your clone has lesson 7.5's town hall video, the video goes up in place of `townhall_2026_q1.md`; the count is the same.

#### What the worker saw

Give it two minutes, then read every request Cloud Run received for the worker since `BURST_SINCE`, by status and by ten-second slice, with the worker's verdicts for the same window:

Three things to check in your output. First, every object was taken in the end: the 200s add up to 31, and the verdicts say `ingest_duplicate` as many times. One more of each is a redelivery, which at-least-once allows and the claim makes harmless. Second, each 429, if you have any, is a delivery Cloud Run refused before the worker saw it, so it has no worker line beside it. The retry policy holds that message back for at least the 10-second minimum before delivering it again (best effort, in Google's words), which is why the 200s spread into later slices. Third, the duplicates are invisible to the kit's lifecycle metric, which counts only ten of the worker's verdicts:

The metric counts `ingest_ok`, `ingest_superseded`, `ingest_reactivated`, `ingest_stale_event`, `ingest_failed`, `ingest_queued_batch`, `ingest_poison`, `ingest_withdrawn`, `ingest_already_current`, `ingest_claim_retaken`. `ingest_duplicate` is not among them, so a burst of 31 deliveries moves `documind/ingest_events` by nothing at all. To count deliveries you need the request log, as above, or Pub/Sub's own metrics, next.

#### What Pub/Sub saw

Pub/Sub keeps its own counts for each subscription: the backlog (messages not yet acknowledged), the age of the oldest of them, and every push it made, by how the push ended. Cloud Run counts its instances the same way. These metrics are sampled every 60 seconds and can take up to 120 seconds to appear (Google's list of metrics), so run this cell at least three minutes after the upload:

The backlog column is the queue's version of what Kafka calls consumer lag: messages published and not yet dealt with. The age of the oldest one is the number an operator pages on, because it grows when the reader is stuck however small the backlog is. The push columns are Pub/Sub's side of the request log: `ack` for every 2xx, `4xx` for every 429 that Cloud Run sent back. The instance column should stay at 5 or under, though Google notes that a spike can take a service past its ceiling for a brief period, so one minute at a little over 5 is not a failure of the squeeze. The last two lines are the proof that the burst did no harm: nothing was forwarded to `documind-ingest-dlq`, and `ingest-dlq-sub` holds nothing, because no message came near 12 refusals.

Notice what the kit itself would have told you about this burst: nothing, and rightly. It has two alerts on this path. One watches `ingest-dlq-sub`. The other, since 13 October 2026, watches `documind-ingest-push`'s oldest unacknowledged message and pages when it stays over 30 minutes for five minutes, so a worker stuck at its ceiling, or down, shows up there about half an hour in, rather than when messages start reaching the dead-letter topic after their twelfth refusal, about an hour after the first by lesson 1.5's clock. A burst that clears in a few minutes, like this one, pages neither. Lesson 8.4 sets that threshold against the slowest turn one document can honestly take.

#### Put the ceiling back

The revision is back at 30, the value `lesson-12.5.sh` holds. The next `make deploy-services` would write it again in any case, because the script, not the revision, is the source. `make dlq` looks at the dead-letter subscription without acknowledging anything, and an empty list is the result you want.

The same burst on Kafka. Five consumers in one group, reading a topic of at least five partitions, would each pull at their own pace. Nothing would be refused and nothing would count against a ceiling of attempts; the backlog would show as lag that rises and falls. That is the real difference between push and pull. On a pushing bus a full reader refuses, and each refusal spends a budget that ends in the dead-letter topic. On a pulling bus a full reader simply reads later, until the records outlive their retention.

### Pub/Sub mapped to Kafka: thirteen rows, and when Kafka would be the better bus

Every setting this page has read, set beside Kafka's nearest concept with the gap between them; then the kit's reasons for its choice, and the point where they stop holding.

Each row starts from what your lane does, as steps 4 to 7 read it, and names Kafka's nearest concept. Kafka's side is its general model and its documented defaults. Pub/Sub's side is the kit's Terraform and Google's documentation, read on 12 October 2026 and linked under the table.

Google's pages behind the Pub/Sub column: subscription properties, push subscriptions, the retry policy, dead-letter topics, ordering, exactly-once delivery, replay and seek, topic retention, subscriptions, Cloud Storage's notices, Cloud Run's pending requests, Cloud Run's maximum instances, Cloud Run's logs, the metrics.

#### Why the kit's choice holds

Read the last column for what the kit would lose by moving, and almost every gap turns out to be covered by something outside the bus. Duplicates are covered by the claim on the content hash, and order by the generation guard, which acknowledges a late notice as stale (both in step 4). Replay is covered by the versioned bucket, which the nightly walk, and `make restore`, replay from by rewriting an object onto itself:

That is the deepest point of the mapping. On Kafka the log is the record of what happened, and replay means moving an offset back along it. In the kit the bucket is the record: every generation of every object, kept by versioning. The bus is only the doorbell, and a doorbell that forgets is fine when the house keeps the parcels.

#### When Kafka would be the better bus

- A second reader that needs the history. An audit consumer, or a pipeline that re-embeds the corpus with a new model, wants every event from the beginning. On Kafka that is a new consumer group set to start from the earliest retained record. On Pub/Sub a new subscription receives only messages published after it exists, so the kit would rewrite every object, or run the walk, to make the events again.

- Order per key. Kafka keeps a partition's records in order, and a key always maps to the same partition, so a consumer that retries a record before it moves on keeps the order. Pub/Sub orders only with ordering keys, which the publisher (here Cloud Storage) would have to set on every notice; a push subscription then holds one outstanding message per key.

- The events as the record. If the events themselves must be kept for longer than 31 days, Pub/Sub's longest retention, or for good, then a log is the store, and on Kafka retention is one topic setting.

- Backpressure without a budget. Step 7's burst: a pulling reader that falls behind lags, while a pushed one refuses and spends attempts. A worker whose documents take minutes each, on a corpus of millions (lesson 8.3's arithmetic), lives better with lag than with a countdown to the dead-letter topic.

- The stream itself as the work. Joins, windows and running totals over the events are what Kafka Streams is built for, reading the same log; a Pub/Sub subscription hands each message to its reader once and then forgets it.

Before any of those, look at what Pub/Sub can do without Kafka. Topic retention (up to 31 days) with seek gives replay. A pull subscriber reads at its own pace, and a pull subscription can have exactly-once delivery. Ordering keys give per-key order. Each is one setting in `eventarc.tf` and one change in the worker. Google Cloud also runs Kafka for you, as Managed Service for Apache Kafka: that takes the brokers off your on-call rota, but not the consumer code, the retry topics or the dead-letter topic, which a subscription gives the kit for nothing. For this lane the threshold is plain. While the bucket is the record and one worker is the only reader, the doorbell is enough; the day a second team needs to replay the events at its own pace, the log has earned its brokers.

### Verify it yourself: the checklist

Eight checks, each one step above, each with what a pass looks like on your lane; then the one command that puts the note away.

When the checks are done, withdraw the note. `make retire` flags its rows as retired, with an `expire_at` 30 days out, marks its ledger row `withdrawn`, removes it from the managed stores, takes its ids out of the Vector Search index (since 13 October 2026) and moves acme's fingerprint. The object stays in the bucket, and `make restore` would bring it back (lesson 1.7):

Then put acme's pin back with the setup section's second window.

One note, `acme/pubsub_trace_note.md`, was indexed and then withdrawn: its three rows are retired and expire in 30 days, its ledger row says `withdrawn`, and the object stays. The thirty-one corpus objects are each one generation newer, with the same bytes: the ledger still names their older generations, so the next walk (`make reconcile`) plans a `touch` for each, which is not drift, and with `APPLY=1` records the new generations. `documind-ingest` has two more revisions, the last at 30 instances as before. acme's pin is back on its managed store. Lesson 8.2 changes the chunker itself, and re-embeds and reconciles what that change touches.

Netsetos GenAI on GCP · Module 8 Ingestion practical · Lesson 8.1 Run the ingest events through Pub/Sub, mapped to Kafka · v5.0

Next: Lesson 8.2 Change a chunker, re-embed and reconcile.
