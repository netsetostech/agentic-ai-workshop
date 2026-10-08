# Lesson 1.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.5_Upload_Events_WIX.html`, reviewed at blob `b5b29878d6f78d5862acedd06fe8cace4972e7ab`. Learners read that page on the course site; this guide keeps its prose.

Lessons 1.1 to 1.4 followed a document from bytes to records and took for granted that the worker was called. This lesson is about the call. An object landing in the bucket becomes a message; the message reaches the worker carrying a token nobody else can mint; the worker answers with an HTTP status; and the platform does one of three things with that status: acknowledges it, tries again after a growing pause, or, after twelve refusals, parks the message where you can read it. Then the one document the push path must not attempt, and the lane that takes it instead.

- What an upload event is

- The words: notification, push, ack, backoff, dead letter, queued claim

- Before you run anything: set up the shell

- The plumbing: read the notification, the topic and the subscription off your lane

- The verdicts: the HTTP-code rule, and your last upload's request log

- Poison: a message that can never succeed, and the retries you can watch

- The batch lane: the 250-page decision, the queued claim, the job

- Dead letters: reading the queue, deciding, cleaning up

- At-least-once, and what it costs

- Verify it yourself: the checklist

You will learn how an upload becomes a delivery (a bucket notification into a topic, a push subscription that calls the worker as the worker's own identity), the one rule that governs every delivery (a 2xx is acknowledged, anything else is retried with exponential backoff until a ceiling of twelve attempts sends the message to a dead-letter topic), and why a document over 250 pages is never attempted on that path but queued for a job on the same image. Then you will prove it on your lane: read the plumbing, read the request log of the upload you made in lesson 1.4, put a message in that can never succeed and watch it retried, list the batch queue, and read the dead letter when it lands.

### What an upload event is

A record about an object, carried by a queue that promises to deliver it at least once, to a worker that answers with a number.

The bucket does not call the worker. When an object is finalized in the uploads bucket, Cloud Storage writes one record about it, the object's name, bucket, generation, size and content type, and publishes that record into a Pub/Sub topic. A push subscription on the topic delivers each record to the worker as an HTTP POST, with an identity token minted for the worker's own service account, so the worker, which allows no unauthenticated caller, accepts the call and nobody else on the internet can make it. The record is the whole message; the worker parses it into the `IngestMessage` contract from lesson 1.1, field for field.

The worker answers with a status, and the status is a decision. Pub/Sub does not read the response body. A 2xx means "delivered, done": the message is acknowledged and never seen again, whether the worker indexed the document, found it already indexed, or handed it to the batch lane. Anything else means "not done": the subscription waits, ten seconds the first time and up to ten minutes later on, and delivers the same message again. It does that up to twelve times. After the twelfth refusal the message is forwarded to a dead-letter topic, where a subscription holds it for a person to read. The worker chooses its answers with this in mind: a message it can never parse gets a 400, because retrying it changes nothing; a failure that might be transient gets a 500, because the next attempt may succeed.

At least once, not exactly once. The queue promises that every record is delivered, not that it is delivered once or in order. A worker that took a long time may see the same message again before it has answered; two workers may receive the same record concurrently; an older version's event may arrive after a newer version was indexed. Every one of these happens on a real lane, and the records of lessons 1.1 to 1.4 are the defence: the claim taken in a transaction makes a duplicate harmless, and the ledger's generation makes a late event harmless. The last defence is a ceiling: a document that cannot finish inside the 600 seconds a push request is allowed is not attempted at all. Its pages are counted first, a claim marked `queued` is written, and a job with no request deadline picks it up.

A courier with a delivery rule. The bucket is the sender; the subscription is a courier who keeps a copy of every parcel until the receiver signs. Sign, and the copy is destroyed. Refuse, and the courier comes back tomorrow, then the day after, then in four days, then in eight, up to twelve visits, and after that the parcel goes to a depot where the sender can collect it. The receiver, who knows this, signs for parcels that are theirs even when the box is empty (a duplicate), and refuses only when refusing is worth another visit. And a parcel too big for the doorstep is not brought to the doorstep at all: the courier leaves a slip, and a lorry comes for it.

#### Follow one delivery

The player below follows one message from the bucket to its end. Pick what the worker answers and watch the path change: the acknowledged verdicts end at a record from lesson 1.4, the refused ones enter the retry clock, whose timings are the subscription's own policy. The clock is arithmetic on the policy, not a measurement; Pub/Sub adds a little jitter of its own.

Every path starts the same way: an `OBJECT_FINALIZE` record, one topic, one push subscription, one POST with the worker's own token. The verdict decides the rest. The retry clock assumes the same verdict every time, which is what a poison message gets; a transient failure usually clears on the second or third attempt.

### The words: notification, push, ack, backoff, dead letter, queued claim

Nine words, each with the value it takes on your lane.

Two of these are lesson 1.4's records seen from the queue's side. The claim is what makes a redelivery a duplicate instead of a second index; the generation on the ledger row is what makes a late event stale instead of a rollback. Lesson 1.7 takes the second one apart; this lesson watches the deliveries that make both necessary.

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

Whether the batch job is declared on your lane is a fact the worker carries in its environment as `BATCH_JOB`. Read it once; step 6 uses it.

### The plumbing: read the notification, the topic and the subscription off your lane

Three resources and two grants, declared in one Terraform file, and the four read-only commands that show them as the platform holds them.

#### Definition

Everything between the bucket and the worker is declared in `terraform/eventarc.tf`: the two topics (the ingest topic and its dead-letter twin), the bucket notification that publishes `OBJECT_FINALIZE` records into the first, the push subscription that delivers them to the worker's URL with an OIDC token, and the subscription that lets a person read the dead letters. Two IAM grants make it work and both fail silently without: Cloud Storage's own service agent must be allowed to publish into the topic, and Pub/Sub's service agent must be allowed to mint tokens as the worker's account. The file's opening comment records that an earlier draft used an Eventarc trigger instead, which delivers a CloudEvent around this subscription, its token, its ceiling and its DLQ; the worker, which parses a Pub/Sub envelope, answered 400 to it.

#### The code

Read the comment above the retry policy: it is the reason the ceiling is twelve, and it is a story from the first live load, not a default.

#### Read it off the platform

You read the same five facts from the platform that the Terraform file declares: one event type, one payload format, one push endpoint that is the worker's URL, one token identity that is the worker's account, and the policy: 600 seconds to answer, 10 to 600 seconds between attempts, twelve attempts, then the dead-letter topic. The worker's own settings close the loop: it answers one request per instance, in at most 600 seconds, on up to thirty instances. Nothing in this step can be changed from here; all of it is what every upload on your lane has been going through since Module 0.

### The verdicts: the HTTP-code rule, and your last upload's request log

The handler that turns a message into a status, its six answers, and the two log records every delivery leaves.

#### Definition

The worker's `push()` handler is the only route the subscription calls. It decodes the envelope, parses the record into the contract, and answers 400 the moment parsing fails, because a message that fails to parse will fail the same way on every retry and the dead-letter queue is where it belongs. Everything after that is a 200 with a different body: `stale` when the ledger already holds a newer generation, `duplicate` when the claim is already taken, `withdrawn` when a person retired the source, `queued_batch` when the batch lane already has it, `already_current` when the other lane seeded the version, `reactivated` for the undo, `indexed` for the ordinary path. Only one thing is a 500: `index_document()` raising after it has released the claim with the error, which is the case where a retry might succeed.

#### The code

The contract's `size` field carries `ge=1`: a zero-byte object fails validation, and validation failing is what makes a message poison. That is the whole mechanism `make poison` exercises in the next step.

#### Read the two records your 1.4 upload left

Every delivery writes a request log entry (Cloud Run's, with the status the worker answered and how long it took) and, from the worker, a JSON line with the verdict. The first read below lists the last few POSTs the subscription made to the worker; the second lists the worker's own verdicts for the same window. Your note from lesson 1.4 should be there twice: once as the duplicate the unchanged bytes produced, once as the indexed version.

Both deliveries were acknowledged, and the request log shows why they looked so different to the worker: the duplicate took a fraction of a second, because the claim was already taken and nothing was downloaded, while the indexed version took several seconds of parsing, embedding and writing. Neither was retried, because a 200 is a 200 whatever the body says. Keep the shape of these two reads: they are how you follow any delivery on this lane, and the next step fills them with a status you have not seen yet.

### Poison: a message that can never succeed, and the retries you can watch

A zero-byte object, the 400 it earns, and the subscription trying again on the clock from step 1. Start this now: the clock runs for about an hour.

#### Definition

A poison message is one the worker refuses before it touches the document, because the record itself is unusable. The kit's drill makes the simplest one: an empty PDF. Cloud Storage publishes its record with `size: "0"`, the contract requires a size of at least one, validation fails, the worker logs `ingest_poison` with the field named and answers 400. From the subscription's side a 400 is a failed delivery like any other, so it retries: after ten seconds, then twenty, then forty, doubling to the ten-minute cap, twelve attempts in all. The worker refuses each one in a fraction of a second and costs nothing. The message, not the object, is what travels; the object sits in the bucket untouched, which is why the last step of this lesson deletes it.

#### The code

#### Do it: start the drill, then watch the first retries

The first block uploads the empty PDF and waits for the worker's first refusal; it prints the validation error the worker logged. Leave a few minutes, then the second block lists every POST the subscription made and every refusal the worker logged since. Note the gaps between the timestamps.

One object produced one message, and the message has been delivered six times in five minutes: the gaps read ten, twenty, forty, eighty and one hundred and sixty seconds, the doubling the policy declares. Every delivery got the same 400 in about thirty milliseconds, because the worker refuses at the contract and never downloads the object. The seventh attempt comes five minutes after the sixth, the eighth ten minutes after that, and from there every ten minutes until the twelfth, about an hour after the first. Then, and only then, the message leaves this subscription for the dead-letter topic. Step 7 reads it there; step 6 fits in the meantime.

### The batch lane: the 250-page decision, the queued claim, the job

The document a push request must not attempt, the record that hands it off, and the consumer that runs the same pipeline without a deadline.

#### Definition

A push request has 600 seconds. Document AI reads about a page a second, so a 400-page contract cannot finish, and a worker killed at the deadline cannot release its claim: the retry finds the claim `processing` and is acknowledged as a duplicate, and the document is stuck until a person notices. The kit refuses to let that happen. Before any page is sent to Document AI, the worker counts a PDF's pages off its page tree (lesson 1.2) and, above `MAX_INLINE_PAGES` (250), writes two records instead of indexing: an `ingest_batch` record with everything needed to fetch the same bytes later, and the claim with status `queued`. The request is acknowledged. The consumer is a Cloud Run job on the very same image, started by the worker the moment it queues (when the job is declared) and by an hourly schedule regardless; it takes each queued claim in a transaction, downloads the bytes by generation, and calls the worker's own `index_document()` with `lane="batch"`, which is how the page ceiling is not consulted a second time. A failure leaves the claim `failed` with the error, and the next run does not retake it.

#### The code

#### Read the lane, Rs 0

The queue is a Firestore query the kit prints for you. The job and its schedule exist only if `BATCH_JOB` was set when the lane was deployed; the box above the setup read it off the worker.

The corpus has no PDF over 250 pages, so the drill makes one: the CGST Act (236 pages) and the IT Act (34) joined with pypdf on your machine, at no cost. Uploading it costs nothing either, and that is the point of the first half: the worker counts 270 pages, writes the queued claim, answers 200, and no page has been sent to Document AI. The second half is where the money goes. When the job is declared, the worker starts it at once and it parses all 270 pages: about Rs 34 on the OCR processor, about Rs 230 on the Layout Parser (at the list prices lesson 1.2 quoted and Rs 85 to the dollar), plus a few rupees of embeddings for roughly six hundred windows. When the job is not declared, the claim simply waits, and `make queued` shows it. Decide before you upload.

With the job declared, the queue empties within minutes and the worker's usual records appear for the bundle, this time with `lane: batch` on the `ingest_ok` line and a `batch_run` line from the job. Without it, the claim stays queued; `make batch-job` declares and schedules the job with a plan through `make plan`'s guard, then its apply (keep `BATCH_JOB=true` on every later `make plan` or `make up`, or the guard refuses the plan that would delete the job), and `make batch` starts a run and waits for it.

You read the batch lane as three records and one job: the queue (a Firestore query, empty unless you took the optional drill), the job (the ingest image with a different command, two hours instead of ten minutes, no platform retries because the claim carries the retry), and the schedule that drains whatever the worker could not start. The decision that feeds it is made before the first rupee is spent, which you saw if you uploaded the bundle: 270 pages counted for free, a claim written, a 200 returned, and the parse belongs to the job.

### Dead letters: reading the queue, deciding, cleaning up

Where a message goes after its twelfth refusal, how to read it without consuming it, and the three things a person can do with it.

#### Definition

A dead-letter topic is not an error log; it is a queue of messages that still exist. When the push subscription has delivered a message twelve times without an acknowledgement, it forwards the message, unchanged, to `documind-ingest-dlq`, and the subscription `ingest-dlq-sub` holds it. Pulling from that subscription without acknowledging shows the message and leaves it there; acknowledging it is the only thing that removes it. A person reading a dead letter has three choices: fix the cause and upload the object again, which is a new event and a fresh twelve attempts; acknowledge the message to drop it, because the object was never meant to be indexed; or leave it while the cause is investigated. What a person must not do is fix the worker and expect the dead letter to retry itself: it is out of the push subscription for good.

#### The code

#### Read it, when it has landed

The poison message from step 5 reaches the queue about an hour after its first refusal. Run the first line then; an empty listing earlier is the retries still running, not a fault. The second read decodes the message's own record, the same JSON the worker refused, to see the size of zero with your own eyes.

#### Decide, then clean up

This dead letter deserves the second choice: the object was never meant to be indexed. Acknowledge the message to remove it from the queue, and delete the empty object from the bucket, because an object with no ledger row is exactly what the nightly walk of lesson 1.8 looks for, and it would rewrite the object onto itself and send the same poison round again every night. Both commands change your lane; both act only on the drill's own artefacts.

You read a message that had been refused twelve times, decoded the record inside it and found the zero that made it poison, and then took the operator's decision: drop it, and remove its cause. Notice what did not need doing: no worker was restarted, no subscription touched, no retry forced. The platform did the retrying, stopped at the ceiling, and kept the evidence for you. A dead letter you could not explain would be the other case, and the first read in step 4, the request log, is where that investigation starts.

### At-least-once, and what it costs

The three ways a delivery can surprise a worker, the defence for each, the one hazard the ceiling exists for, and where the rupees go.

#### Three surprises, three defences

#### The hazard the ceiling exists for

There is one failure the claim cannot defend against on its own. A request that runs past 600 seconds is killed by the platform, not by the worker, so the code that releases the claim never runs. The claim stays `processing`; the subscription retries; the retry finds the claim taken and is acknowledged as a duplicate; and the document is never indexed while every delivery reports success. The 250-page ceiling is the answer: no push request is allowed to begin a document that could reach the deadline, and the job that takes such documents has two hours and no platform retries, because a failed document says why on its claim and the next run does not retake it. Lesson 1.8's reconcile is the backstop that would notice a claim stuck in `processing`.

#### What deliveries bill, and what they do not

The asymmetry to remember: the delivery machinery is nearly free, and the expensive thing is the document, which is why the kit spends nothing before it knows what it is dealing with: parse the record before downloading, count the pages before parsing, take the claim before embedding. Every refusal in this lesson happened before the first rupee.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

One empty object, uploaded and then deleted; one dead letter, read and then acknowledged; and, only if you took the optional drill, one 270-page bundle under acme with its own records. Everything else was read. Lesson 1.6 goes back to a document that is already indexed and changes one clause of it, to see exactly what a re-issue costs.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.5 Follow upload events, retries, dead-letter handling and the batch lane · v5.0

Next: Lesson 1.6 Reindex a changed section and measure embedding reuse.
