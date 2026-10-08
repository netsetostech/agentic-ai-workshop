# Lesson 3.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.8_UI_Journey_WIX.html`, reviewed at blob `f27f9d0481047e5469cc8e52c3997f8bea47a544`. Learners read that page on the course site; this guide keeps its prose.

Lessons 3.4 to 3.7 built the answer. This lesson puts a screen in front of it and walks the whole journey once, as a person. You sign in through IAP, and the UI knows who you are from a signed assertion, never from a form. It finds your tenant on the roster. You upload a note on the Documents page, and the UI writes it into your tenant's folder as its own service account. The worker indexes it, and the Versions table shows the version the ledger now holds. You ask about the note in Chat: the answer streams from the API, the sources render as pills before the first word, and each source opens through a link that is signed for 15 minutes. The API believes the person, not the page: the usage row names you. You will check each hop from the shell as you make it in the browser.

- What the page does, what it never does, and who each hop runs as

- The words: IAP, assertion, roster, watched prefix, Versions, stream, pill, signed URL, surface, the row's user

- Before you run anything: set up the shell

- The front door: IAP, the UI's settings, and who may sign in

- The upload: a note you write, uploaded in the browser, followed to the ledger

- The answer: asked in Chat, streamed, and the row that names you

- Citations: the pills, the sources, and the link signed through IAM

- The UI's account: what it may do, and the checks the page makes first

- What the journey costs, the sidebar's own price table, and what nothing records

- Verify it yourself: the checklist

You will learn how the Streamlit UI signs a person in, finds their tenant and writes their upload, and why every answer it shows comes from the API rather than a model of its own. You will also learn how the sources are drawn and opened. Then you will prove it on your lane: upload a note in the browser and follow it to the ledger, ask about it in Chat, open its source through a signed link, and read the usage row that names you and not the UI.

### What the page does, what it never does, and who each hop runs as

A thin client with three jobs: sign a person in, drop their file where the worker watches, and show what the API says.

The UI is a thin client with three jobs. It signs a person in, it writes an upload into their tenant's folder, and it shows what the API says. Everything else happens elsewhere. The worker indexes. The API retrieves, reranks, packs, generates, cites and prices. The ledger and the index belong to those two services. The chat page makes no model call, by design, and neither does the Documents page. The Studio tab posts to the API as well. The only Google model the UI calls itself is Speech, for voice input and read-aloud. So a change to the prompt, the model or the retrieval never needs a UI deploy, and a bug in the UI cannot quietly change an answer.

Four identities make the journey, and each hop runs as one of them. The person signs in with Google at IAP, which sits in front of the UI's run.app URL. IAP passes each request to the container with a signed assertion that names the person, and the page verifies it for its own audience. The UI's service account, documind-ui-sa, writes the upload into the bucket and mints an ID token to call the API. It also signs the source links, through IAM. The worker's account reads the upload and writes the rows, and it is the only indexing writer. The API's account reads the rows. Every call from the page to the API carries two credentials: the UI's token, which gets it past Cloud Run, and the person's assertion, forwarded unchanged. When both arrive, the API believes the assertion. The roster check and the usage row are therefore about the person, and the page is just the road they came in by.

The page is honest about what it knows. "Upload complete" means the object is in the bucket, not that it is indexed, and the page says so. The Versions table is the ledger, read through the API, so a document shows there only once the worker has written its row. The sources arrive before the first word of the answer, because they are the packed set. Each pill is the number the model cited, and its source opens through a link that expires after 15 minutes.

The front desk of a bank. Security checks your photo ID at the door and gives you a visitor tag with your name on it. That tag is IAP's assertion. The teller at the front desk is the UI. The teller looks up your company's account by your name, drops your deposit into the intake tray under that account, and never opens the vault. The back office processes the tray. That is the worker. The passbook shows only what has cleared. That is the Versions table. When you ask a specialist a question, the teller walks it over with your tag clipped to it, so the answer and the logbook carry your name, not the teller's.

#### The journey: seven hops, the identity on each, and what proves it

- the personsigns in with Google at IAP, which fronts the UI's run.app URL and admits only accounts granted the sign-in rolean unsigned request gets HTTP 302 to Google's sign-in

- documind-uiverifies the assertion for `IAP_AUDIENCE`, then finds the tenant on the roster: `tenant_for(email)`your email and tenant in the sidebar

- documind-ui-sawrites the upload to `gs://PROJECT-uploads//`, the watched prefixthe object and the generation the page reports

- documind-ingest-sathe object's event reaches the worker, which parses, chunks, embeds, and writes the rows and the ledger`ingest_ok` with the file's own hash in the key

- ui-sa + the personthe Versions table: `GET /v1/sources` with the UI's token and your assertionthe new row, `indexed`

- ui-sa + the personChat: `POST /v1/stream` with brain `ui`; the API checks the roster against youthe usage row's `user` is your email

- documind-ui-sathe pills from the packed set; Open source is a V4 link signed through IAM's signBlobthe link opens, then expires

Rows 3 and 7 run as the UI's account alone; rows 5 and 6 carry the person's assertion beside it. Step 3 checks row 1, step 4 rows 2 to 5, step 5 row 6, and step 6 row 7.

#### The citation renderer: the UI's pills and sources, from a transcript you paste

The chat page draws the answer with `render_with_citations()`. Each `[N]` in the answer becomes a pill: text sources get plain numbers, figures and tables get their kind and page, and video segments get their start time. Hovering a pill shows the start of its source. Under the answer, a Sources list offers each source's link. The renderer below is that function in the page, reading the transcript `curl -N` prints for `/v1/stream`, the same events the UI reads. It starts on a sample built from this lesson's own note. The cases show the other shapes, including two that surprise people.

The rules are ported from `services/frontend/citations.py`: the `[N]` pattern, the pill labels, and the Sources list with its effective-from line and link labels. The sample's sources are the note's chunks and two handbook sections, cut by the kit's chunker. The bench escapes the answer's text before drawing pills. The UI does not, as step 6 explains.

It cannot sign a link, so it names the object a link would open. It maps `[N]` to the Nth citation event, as the UI does, and that holds only for a stream: a `/v1/query` answer lists the citations the model used, in its own order. Step 6 gives you a transcript of your own to paste.

### The words: IAP, assertion, roster, watched prefix, Versions, stream, pill, signed URL, surface, the row's user

Ten rows, each with the value it takes on your lane.

One distinction to hold: signing in and membership are two checks by two systems. IAP decides who may reach the page at all; the roster decides which tenant's documents a person may see. An account can pass the first and fail the second, and the page then says so instead of showing an empty tenant.

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

The UI's own environment says how it signs people in, where it uploads and which API it calls. The block prints the five names that matter and exports the UI's address for the steps below. An empty `CHAT_URL` means the chat service is not deployed on this lane, and then Chat has no brain picker. The page streams from the API directly, which is the journey this lesson follows.

### The front door: IAP, the UI's settings, and who may sign in

The deploy line that puts IAP on the service, the page's check of the assertion, the roster lookup, and a request that never reaches the container.

#### Definition

The UI is deployed with IAP turned on for the service itself. The run.app URL is the front door. IAP signs people in with Google and admits only accounts granted the sign-in role. The service admits no unauthenticated callers, and IAP's own service agent is its only invoker, so a request without a sign-in never reaches the container. Every request that does reach it carries the assertion. `current_user()` verifies it against Google's IAP keys, for this service's audience, and reads the email from it. `tenant_for()` then looks the email up on the roster: one query across every tenant's members, run on every page load and never cached. So a person taken off a roster loses the tenant, and the upload right that comes with it, on their next click. A person who can sign in but is on no roster sees a sentence saying so, not an empty tenant.

#### The code

#### Do it: the service's account, IAP's flag, who may sign in, and a request without one

Now open the address in your browser and sign in as a roster member. The sidebar shows your email, and Chat's sidebar shows Tenant: acme. Those two lines are `current_user()` and `tenant_for()`, one below the other.

The shell asked the front door without signing in, and IAP answered by sending it to Google's sign-in. The container behind it logged nothing, because nothing reached it. Your browser, signed in, got through with an assertion, and the page read your email from it after checking IAP's signature and the audience. It then found your tenant on the roster with a query it runs on every page load. Signing in and membership are two gates run by two systems: the sign-in list lives in IAP, and the roster lives in Firestore.

### The upload: a note you write, uploaded in the browser, followed to the ledger

What the Documents page writes and where, the worker's line for your bytes, and the Versions row the ledger serves.

#### Definition

`upload_document()` refuses a tenant or a file name that could escape the tenant's folder. It also refuses a file type outside its list of 9 extensions. Then it writes the object to `/` in the uploads bucket as the UI's account, with a content type and nothing else, and reports the generation the bucket assigned. That is all the page does. The object's event reaches the worker, and the rest is Module 1: parse, screen, chunk, embed, write the rows, and write the ledger row keyed by the bytes' hash. The Versions table asks the API for the ledger with the page's two credentials, so a document appears there only after the worker has written it. That is why the page tells you to refresh rather than claiming success. The note you upload carries a line with your account and today's date, so its bytes are new to the lane and the worker embeds it. Lesson 1.1 uploaded the kit's amendment the same way, and uploading that file again would only be acknowledged as a duplicate.

#### The code

#### Do it: write the note, upload it in the browser, follow it

First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault.

In the browser, open Documents, choose the file, and click Index documents. The page reports the object it wrote and its generation, then says the upload is complete and indexing is still in progress. Wait half a minute and click Refresh indexing status until the note appears in Versions. Then follow it from the shell:

You gave the page a file, and it did the one thing it is allowed to do: it wrote the file into your tenant's folder as its own account, with a content type. The bucket's event woke the worker, which found bytes it had never seen, cut them into 3 chunks, one for the title and one for each clause, and embedded all three. Its key ends in your file's own hash, so the ledger row is about exactly the bytes you wrote. The Versions table showed the row only after the worker had written it, because the table is the ledger, served by the API.

### The answer: asked in Chat, streamed, and the row that names you

The two credentials on every call, the stream the page reads, and the usage row that says who asked.

#### Definition

Every call the page makes to the API carries two credentials. `_headers()` mints the UI's own ID token for the API's address, which gets the call past Cloud Run, and it forwards the person's assertion unchanged. `stream_answer()` posts the question to `/v1/stream` with the label `brain: ui`, and it yields each event as it arrives. The chat page keeps the citation events as sources, writes the tokens into the answer as they come, and accepts the answer only when `done` arrives. A stream that ends early is shown as a failure, never as an answer. On the API's side, the shared identity check reads the assertion first. The person is the caller, the roster is checked against them, and the usage row's `user` is their email. A request from the shell carries the UI's token alone, so its row names the account. Both rows read `brain: ui`, because the API records a request that names no brain as `ui`. `user` is the field that tells them apart.

#### The code

#### Do it: ask in the browser, ask from the shell, read both rows

In the browser, open Chat and ask: What colour badge do visitors wear at the Pune warehouse? The sources arrive first and the answer streams after them. The answer ends with a pill. Hover over it to see the note's clause, and open Sources under the answer. Then ask the same question from the shell and read the two newest rows:

The same question went in twice by two roads, and the rows show which was which. From the page, the API saw the UI's token and your assertion, and it believed the assertion. The row names you, the roster was checked against you, and nothing in the page could have claimed otherwise. From the shell, only the UI's token arrived, and the row names the account. Both rows say `ui` in the brain column, which is why that column tells you nothing about who asked. Both answers cite the note you uploaded minutes earlier: in one sitting, the journey took your file from the bucket, through the ledger and the index, to a cited answer.

### Citations: the pills, the sources, and the link signed through IAM

How an [N] becomes a pill, what the Sources list offers for each kind, and why the UI's account can sign a link without holding a key.

#### Definition

`render_with_citations()` finds every `[N]`, or `[N, M]`, in the answer. It matches each number to the Nth citation event and draws a pill. The label is a plain number for text, a kind and page for a figure or a table, and a start time for a video segment. A number past the last source still gets a pill, marked as an unknown source. The pattern accepts digits only, so a model that writes `[Source 1]`, copying the context's headers, gets no pill at all. The Sources list shows each source's label, the start of its text, and its effective date when the ledger stamped one. Below that sits a link. A figure's link shows the image inline, a segment's plays the video from its start, and text gets Open source, or Jump to page N when there is a page. Every link is a V4 signed URL valid for 15 minutes. A Cloud Run service has no private key to sign with, so the page hands the library its own email and access token, and the library signs through IAM's signBlob API. That works because the account holds the token-creator role on itself.

#### The code

#### Do it: open the source, then render your own transcript

In the browser, under the answer from step 5, open Sources and click Open source on the note. A new tab shows the note's text from the bucket, through a link that stops working in 15 minutes. Then capture the same answer as a transcript and paste it into the renderer in step 1:

The link opened because the UI's account signed it through IAM, for one object, for 15 minutes. No key was stored anywhere, and anyone holding that link could read that one note until it expired. The transcript you pasted was drawn exactly as the page draws it. The `[1]` in the answer became a pill whose hover shows the note's badge clause, because the first citation event is the first packed chunk. The Sources list offered Open source, not Jump to page, because a markdown note has no pages.

### The UI's account: what it may do, and the checks the page makes first

The roles the UI's service account holds, the ones it pointedly does not, and the grants that let it upload, call the API and sign links.

#### Definition

The UI's account holds a short list of project roles: Vertex AI and Document AI users, the Secret Manager accessor, Firestore user for the roster, and Speech for voice. It also holds object admin on two buckets, the uploads and the text-to-speech cache, and the token-creator role on itself, for signing. It holds no project-wide invoker role. The API and the chat service each grant the UI's account the right to call them, and that is the whole call graph. It holds no BigQuery role either, and the Terraform says why: the process that renders user chat should not hold warehouse credentials, because a flaw there would reach the warehouse. The page adds its own checks before anything is written. The tenant comes from the roster, never from a form, and must be a plain name. The file name must be plain, with no path, no control characters and at most 255 bytes. The extension must be on the list, and one upload is capped at 200 MB.

#### The code

#### Do it: read the account's grants, Rs 0

The account's grants read like the journey's hops. Object admin on the uploads bucket is the upload. Invoker on the API is the Versions table and the chat. The token-creator role on itself is the signed links. Firestore access is the roster lookup. The worker is not something the UI may call: it runs when the bucket says an object arrived, and the UI's only way to start it is to write a file where it watches. A missing `documind-chat` prints "no such service" on a lane without the chat service. That is expected, not a gap.

### What the journey costs, the sidebar's own price table, and what nothing records

The rupee line, a second price table inside the page, the answer drawn as HTML, and the uploader nobody writes down.

#### What it costs

#### The sidebar's own price table

The sidebar's "Cost this session" is not the bill. The stream's `done` event carries tokens but no price on the vertex backend, so the page prices each turn itself. It multiplies the tokens by two rates written into its own code, $1.50 in and $7.50 out per million, at 85 rupees to the dollar. The API prices the same tokens with `cost.py`, which reads a price table and charges cached input at a tenth of the rate. The two agree today. After a price change, the sidebar stays wrong until the image is rebuilt. Once Module 6 turns a context cache on, the sidebar overstates, because it charges cached tokens at the full rate. The usage row is the bill, and the sidebar is an estimate.

#### The answer, drawn as HTML

To draw the pills as badges, the page renders the whole answer with Streamlit's `unsafe_allow_html`. The model's text becomes HTML, and the hover text escapes only quotation marks. A model's output is text the page did not write, and this is one reason the Terraform keeps warehouse credentials out of the UI's process. The renderer in step 1 escapes the answer before it adds pills, which is the safer order.

#### What nothing records

The page knows who uploaded a file: it just read your email off the assertion. Nothing writes that down. The object is written by the UI's account with a content type and nothing else, and the ledger row carries the tenant and the version, not the person. A storage audit log, where one is switched on, would name the UI's account. So the lane can tell you which version of the note is current and when it landed, but not who put it there. Recording the person means stamping the email onto the object, a one-line change to the kit that this course has not made.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

One new document under acme, `pune_visitor_rules.md`, indexed with 3 chunks. It answers a question no golden row asks, so it can stay. To withdraw it, run `make retire PROJECT=$PROJECT SOURCE=acme/pune_visitor_rules.md`. Your questions are usage rows, one of them with your email on it, and the transcript is at `/tmp/stream64.txt`. The journey from an upload to a cited answer now works end to end on your lane. Lesson 3.9 designs a fact-checking system from these parts, and Module 4 then measures how good the answers are, starting with the questions it measures them on.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.8 Complete the Streamlit upload-to-answer journey · v5.0

Next: Lesson 3.9 System design: a fact-checking system built from DocuMind's parts.
