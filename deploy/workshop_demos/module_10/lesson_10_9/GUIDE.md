# Lesson 10.9: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.9_Managed_Agents_WIX.html`, reviewed at blob `b1e042febecc4ac43357ffb2c6605c2c20722e94`. Learners read that page on the course site; this guide keeps its prose.

Lesson 10.6's peer runs on Cloud Run, and two accounts may call it. This lesson runs the same peer on Vertex AI Agent Engine, Google's managed runtime for agents. The kit copies `services/agent/agent.py` byte for byte and changes one setting outside it: where the model is called. The peer still runs as `documind-agent-sa`, on acme's roster alone, so it reads what it read before. Two things change. Another agent asks it through the platform's query API, not A2A, and every account that holds Vertex AI User on your project may ask. You stage the package and print every call for Rs 0. Then you deploy it, ask it on both hosts, read what the asks left, run the proof, and tear it down.

- One peer, two hosts, two doors

- The words: Agent Engine, instance, query API, service agent, session, user id, GlobalGemini, the seam, probe fact

- Before you run anything: set up the shell

- What up stages, and what the runtime will import

- Every call through one seam: the dry run

- What the kit rests on: the author's probe

- Deploy, and ask through the query API

- What the asks left: spans, log rows and sessions

- The proof: make managed-peer-smoke, and the comparison

- Cloud Run or Agent Engine, what it costs, and what the kit does not do yet

- Tear it down, and verify it yourself

You will deploy lesson 10.6's peer, unchanged, to Agent Engine and ask it the same questions on both hosts. You will see what stays the same (its account, its roster, its answer) and what changes (the protocol, who may call it, the sessions), prove it with `make managed-peer-smoke`, and leave nothing billing.

### One peer, two hosts, two doors

The same agent and the same reach; a different door, and more kept on Google's side.

The same peer. Agent Engine runs an agent you hand it as a package. The kit's package is the peer's own `agent.py` and `requirements.txt`, copied byte for byte, with a short wrapper as the package's `__init__.py`. The wrapper hands the platform the peer's own agent object and changes one thing: its model's client always calls location global. The platform sets `GOOGLE_CLOUD_LOCATION` to the instance's region, and Gemini 3.x is served only from global. google-adk's own deploy, at the peer's pin, sends the package with a Dockerfile of ADK's, and the platform builds the image and runs it.

The same reach. The runtime runs as `documind-agent-sa`, the account the Cloud Run peer runs as. The lesson plan's decision 13 keeps that account for the cohort: no new account and no Terraform. The peer reaches the lane only through `documind-mcp`, with an ID token for that address, and the server finds the account on acme's roster alone. Whoever asks, the answer is acme's, and a question naming zeta is refused by the roster, as on Cloud Run.

A different door. On Cloud Run, another agent reads the card and sends `message/send` with an ID token for the peer's URL, and Cloud Run admits two accounts. Agent Engine serves no card. A caller sends `streamQuery` to Google's own API with an access token, and IAM checks one permission, `aiplatform.reasoningEngines.query`. Vertex AI User carries it, and on the lane five accounts hold that role across the whole project. Unless an instance can carry an IAM policy of its own, which is fact 8 of the author's probe, every one of them may ask. `make managed-peer-up` lists them.

More is kept on Google's side. Each question opens a managed session, filed under a user id the caller writes in the request. Spans go to Cloud Trace, with message content off. The instance exists until it is deleted, at a price the kit does not state (fact 12), so the kit tears it down by default: the smoke deletes what it deployed, and `make managed-peer-down` deletes the rest.

Your own canteen against a managed caterer. Today your canteen cooks for the office, and its door admits two badge holders. A caterer can run the same kitchen: the same cook, the same recipe, the same supplier account, so whoever orders gets the same food. But the caterer's gate admits anyone with a building pass. You still decide who gets a building pass, and which supplier account the cook buys with. The caterer also keeps every order slip, filed under the name the customer writes on it, and it bills you for as long as the kitchen stays open.

#### Who may ask the peer

Choose a caller, one of the lane's accounts. The panel shows each host's door, then what the peer does for a caller it admits. The table under it sets the two hosts side by side, each cell with the file, or the probe fact, it comes from.

Each door is the kit's own: Cloud Run's from `commands/lesson-8.4.sh`, Agent Engine's from the project roles in `terraform/sa.tf` and the roles `managed_peer.py` counts as carrying the query permission. The panel leaves out `documind-admin-sa` and the CI account. Neither holds a role the kit counts as carrying the query permission, and both hold Cloud Run Developer, which the kit does not reason about at Cloud Run's door.

It asks nothing. Each door is a binding or a role the kit writes, read when this page was built. Whether Agent Engine honours them the way the kit expects is what the author's probe and your smoke check, and a cell that names a fact changes with the author's table.

### The words: Agent Engine, instance, query API, service agent, session, user id, GlobalGemini, the seam, probe fact

Twelve rows, each with the value it takes on your lane.

One distinction to hold. An ID token says who you are to one URL, and Cloud Run checks it at that URL. An access token says who you are to Google's APIs, and IAM checks it against the project's policy. The Cloud Run peer takes the first. The managed peer takes the second, so its door is the project's IAM.

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

The shell, in the kit's folder, with `PROJECT`, `REGION` and `NUMBER`. Steps 3 to 5 need nothing more and cost Rs 0. Steps 6 to 10 need the lane deployed by `make up`, with the Cloud Run peer and `documind-mcp`, and `make operators` from lesson 0.3, which lets you mint tokens as `documind-ui-sa` and `documind-outsider-sa`. Step 6 creates an instance that bills until step 10 deletes it, so run steps 6 to 10 in one sitting.

### What up stages, and what the runtime will import

The peer's files, a wrapper, a config and an environment; then the package imported as the platform imports it.

#### Definition

`stage` writes out what `make managed-peer-up` deploys, without deploying it. It copies the peer's two files and the wrapper into a folder named `documind_peer`, a Python identifier because ADK's loader imports it. Beside the folder, not in it, it writes the deploy's `.agent_engine_config.json` and `.env`, so neither ships in the package. It reads the model from `commands/lesson-8.4.sh` and makes no call.

#### The code

#### Do it: stage

Six files, byte for byte: `agent.py` and `requirements.txt` are the Cloud Run peer's own, `chain.py`, `pins.py` and `tool_pins.json` are agent.py's own modules and data (lessons 10.7 and 10.8), and `__init__.py` is the wrapper. The config names the runtime's account and asks for at most one instance, with none kept warm. The `.env` carries the Cloud Run peer's own `MCP_URL` and `AGENT_MODEL`, and the cap.

Four of the Cloud Run peer's variables stay behind. `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` are reserved by the platform and set by ADK's Dockerfile, the location to the region, which is why the wrapper exists. ADK's `GOOGLE_GENAI_USE_ENTERPRISE=1` plays the part of `GOOGLE_GENAI_USE_VERTEXAI`. And `SELF_URL`, the card's address, has no use here, because no card is served. The last line is ADK's own Dockerfile. It installs google-adk at the peer's pin, then the requirements, to which the deploy appends `google-cloud-aiplatform[adk,agent_engines]`, with no version unless `AIPLATFORM_PIN` is set (fact 11).

#### Do it: import the package as the runtime will

The image runs `adk api_server`, which imports the package and serves the `root_agent` it finds there. The cell makes the same import with ADK's own loader, in a venv holding the peer image's pins. It sets the location ADK's Dockerfile sets and the content setting ADK's deploy adds, and reads no `.env`, since the image ships none. It makes no call: the model and the tools are reached only when a question arrives.

ADK's loader found `root_agent`, and it is `agent.py`'s own object, the one the A2A app serves on Cloud Run, with the peer's MCP toolset. Its model is `GlobalGemini`, and ADK's run config read the cap from the environment. The first line is the wrapper's: the location the platform set, the model's location, the cap, content capture, and the versions the image installed. `make managed-peer-trace` reads the same line from the runtime's log, and the smoke's eighth check holds it to global, 12 and false.

### Every call through one seam: the dry run

Each Google call printed before it is made; with DRY_RUN=1, printed and not made.

#### Definition

Every call the kit makes to Google passes through one method, `Seam.call()`. It prints the call, then makes it. With `--dry-run` it prints the call and returns a stand-in value, so no backend is built and no Google library is imported. `DRY_RUN=1` runs the targets with the kit's own python rather than `~/managed-peer-venv`: no credential, nothing created or changed, Rs 0. The kit's tests replace the backend the same way.

#### The code

#### Do it: up, printed

8 calls, in the order a live `up` makes them. It looks for an instance by its display name, then creates an empty one and records it before anything else can fail, so `down` can find it. It reads the project's number for the service agent's address, then reads and rewrites `documind-agent-sa`'s IAM policy to add the grant. Then come google-adk's own deploy, a read back of what the platform kept, and the project's policy, read for who may query. The two closing lines print on every live `up` too: what bills while the instance exists, and who may call it.

#### Do it: one question, as each host is asked

The same question, two protocols. The managed peer is asked on Google's regional endpoint: `streamQuery` with the class method `async_stream_query`, as `documind-ui-sa`, and the body carries a user id the caller chooses. The Cloud Run peer is asked at its own URL with `message/send`, as `make smoke-agent` asks it, with an ID token minted for that URL. The first needs a role on the project; the second needs the invoker binding on the service.

#### The records, and the table they feed

Every live run appends one record to `evals/reports/managed-peer/runs.ndjson`, which git ignores. A record holds the latency to the first event and to the last, whether the call was the first after a deploy and how long the host had idled, the region, the runtime's account, the caller and the door, the model's tokens and rupees where the reply carries them, and the host's scaling and price. It names no project, project number or instance, and `JSON=1` prints it. `compare` turns the records into one table.

Two kinds of cell. The region, the account, the door and the hosting come from the kit's own files, so they are filled before any run. The timings and the peer's rupees come from your runs, and step 8 fills them.

### What the kit rests on: the author's probe

11 rows no lane had shown when the kit was written, and what a refusal does to each.

#### Definition

No lane had run the managed peer when the kit was written, on 13 October 2026. Everything it assumes about Agent Engine is a row of `FACTS`, and each row is a fact the author's probe settles. The probe, `tools/probe_agent_stack.py`, lives in the authoring repository and is never published. It runs in batch 0 (Mon 19 - Wed 21 Oct 2026), creates what it tests, deletes it, and writes a dated table: each fact observed, refused in the API's own words, or not tested, with the reason.

#### The code

#### The author's facts table

The kit exits with one of five codes: 0 done, 1 a check failed, 2 stopped (a missing precondition, or a refusal that settles no fact), 3 a fact refused, 4 something could not be deleted. A refusal is read against the facts before it is reported. A refused deploy that names an `iam.serviceAccounts` permission is fact 2, with the make line that grants the role carrying it. A refused region is fact 1, with `MANAGED_PEER_REGION=us-central1`. An image that did not build is fact 11, with `AIPLATFORM_PIN`. A 403 on a question is fact 8. A turn whose runtime minted no ID token is fact 5, and a model looked up in the region rather than on global is fact 6.

`mk/managed.mk` declares the three settings the table decides: `MANAGED_PEER_REGION` (your `REGION` by default), `MANAGED_PEER_GRANT_ROLE` (`roles/iam.serviceAccountTokenCreator`) and `AIPLATFORM_PIN` (empty, so unpinned). Where a fact fails on your lane, this page keeps the author's dated capture for that cell.

### Deploy, and ask through the query API

The dry run's calls, made; then one question, three ways.

#### Definition

`make managed-peer-up` makes the calls the dry run printed. The first time, it makes `~/managed-peer-venv`, with google-adk at the peer's pin and google-cloud-aiplatform, which ADK's deploy and the Agent Engine client import. The kit puts the deploy at 10 to 20 minutes, most of it the image's build, and it prints its progress as it goes. Run it again and it does nothing unless `REDEPLOY=1`.

`make managed-peer-ask` sends `make smoke-agent`'s question as `documind-ui-sa`. Run it three times: for acme, which is answered through `documind-mcp`; with `TENANT=zeta`, which the roster refuses; and with `HOST=cloudrun`, which asks the Cloud Run peer the same question over A2A and measures it the same way.

#### The code

#### Do it: deploy

The lines come in the dry run's order, with `call:` where the dry run said `would call:`, and ADK's own progress in the middle. The read back shows what the platform kept. `serviceAccount` should be `documind-agent-sa`. `minInstances` may read absent, because the API's JSON leaves out a zero, so 0 and unset look alike. `maxInstances` should be 1, and `env` lists the variables' names. WHO MAY CALL IT names the service accounts that hold a role carrying the query permission, and counts the people. On the course's lane, `terraform/sa.tf` gives Vertex AI User to five accounts: `documind-ui-sa`, `documind-api-sa`, `documind-ingest-sa`, `documind-chat-sa`, `documind-agent-sa`. Your project may add more, and each one may now ask the peer.

#### Do it: ask, three ways

acme's question came back as a turn: the call to `retrieve`, its result, the answer, and a verdict against `make smoke-agent`'s expected answer, five years. The timing line gives the first event and the last. The cost line gives the peer's own model calls in tokens, priced at `shared/prices.py`'s list price: gemini-3.6-flash at USD 1.50 in and 7.50 out per million tokens, thinking billed as output, Rs 85 to the dollar. `first call after the deploy: True` marks the first question since the deploy, the one an idle instance would slow (fact 4).

zeta's question reached `documind-mcp` as `documind-agent-sa`, and the tool's result carries the server's own refusal: the account is not on zeta's roster. The peer relayed it. The Cloud Run peer answered the same question over A2A. `message/send` returns once, so only its total is timed, and its tokens come from the usage ADK's A2A converter writes into the task's messages.

### What the asks left: spans, log rows and sessions

Cloud Trace, Cloud Logging and the sessions API, read the way the kit reads them.

#### Definition

`make managed-peer-trace` reads three places and changes nothing. In Cloud Trace, the spans of every trace that holds ADK's `invoke_agent documind_peer` span, polled every 20 seconds for up to `WAIT` seconds, 120 by default, because spans take a while to appear. In Cloud Logging, `documind-mcp`'s `mcp_call` rows. And in the runtime's own log, the wrapper's line. By default it reads the window of your last managed question and checks that none of its words is in any span. `SINCE=15` reads the last fifteen minutes instead, so the rows cover both hosts' questions from step 6; the smoke checks the words.

`make managed-peer-sessions` lists the instance's managed sessions by user and reads the newest event by event. Then it reads the same session as another user, and once more through the API's own read, which names no user.

#### The code

#### Do it: trace

`documind-mcp`'s rows name `documind-agent-sa` for both acme questions, the managed one and the Cloud Run one, and name nothing else. The server cannot tell the two hosts apart, nor the caller behind either. zeta's question left no row: the roster refuses before the row is written. That shared name is the trade-off in the plan's decision 13: no new account and no Terraform, and in exchange one identity in the server's logs for two hosts.

The runtime's own line is the one step 3 printed offline, now from the platform: the region it set, the model on global, the cap, and the versions its image took, google-cloud-aiplatform's among them.

#### Do it: sessions

Each managed question opened a session, filed under the user id the caller wrote: `documind-ui-sa`. Read as `another-user`, ADK's session service refused it, but in the client and after the read: it fetches the session, then compares the user id. The API's own read names no user, and it returned the session. So what keeps one caller from another's sessions is IAM on the instance and that client-side check, not the API (fact 9: awaiting the author's probe).

### The proof: make managed-peer-smoke, and the comparison

Eight checks on the managed peer, the Cloud Run peer asked the same way, and your table.

#### Definition

`make managed-peer-smoke` is the lesson's proof. It asks as `documind-ui-sa` and runs eight checks:

- acme answered through `documind-mcp`: the expected answer, and a call to `retrieve`.

- acme answered again, warm.

- zeta refused by the roster.

- The outsider refused by the platform: `documind-outsider-sa` holds no project role, and a 403 passes.

- `documind-mcp`'s rows during those questions name `documind-agent-sa` alone.

- Spans written, with neither question's words in them.

- Sessions kept, and another user refused by ADK's check.

- The runtime's line: the model on global, the cap of 12, content capture off.

Then it asks the Cloud Run peer the same three questions and prints the table from the records. With no managed peer it deploys one first, and deletes it at the end unless `KEEP=1`. Here step 6's peer exists, so the smoke uses it and leaves it for step 10. A check that cannot run yet is a SKIP with its reason, since spans and log rows can take minutes to appear. The smoke exits 1 when a check fails.

#### The code

#### Do it: the smoke

#### Do it: the table, from your records

Eight passes are the proof: the same peer, answering from acme's corpus through `documind-mcp` as `documind-agent-sa`, refusing zeta by the roster, closed to an account with no role, with message content out of the spans and the cap read where the model runs. The table sets the two hosts side by side from your own records: the first call after a deploy, the warm median and the slowest, the peer's own rupees, the account and the door. rag-api's answer inside `retrieve` is billed on the lane whichever host asks, so it is in neither column.

### Cloud Run or Agent Engine, what it costs, and what the kit does not do yet

Choosing a host with your numbers, the bill, and the gaps the build asserts.

#### Choosing a host

- The reach does not move. Both hosts run the peer as `documind-agent-sa` on acme's roster, so the host never changes which documents the peer reads.

- The door does. Cloud Run's is two named invokers. Agent Engine's is every holder of Vertex AI User on the project, five of the lane's accounts and anyone your project adds, unless fact 8 shows that an instance can carry a policy of its own. The peer has no roster of its own, so its door is all that stands between a caller and acme's documents (lesson 10.6).

- The protocol. A2A gives other agents a card to find the peer by. The query API gives Google's clients and managed sessions, and no card: an agent that speaks only A2A cannot find or call the managed peer.

- What the platform adds. Sessions kept per user id, spans with message content off, an image built from the peer's own requirements, and a cap set without touching `agent.py`. On Cloud Run the peer keeps its sessions in memory, inside each instance; its cap is the same 12 model calls a turn, set by `commands/lesson-8.4.sh` and kept by `agent.py` when nothing sets it (lesson 10.7), where ADK's own default would be 500.

- Time and money. Your table's first and warm calls are the latency, measured the same way on both hosts. Cloud Run bills by request time, like the lane's other services; Agent Engine's price is fact 12.

- A third host, documented and not run. google-adk 2.8.0's deploy also has a GKE target, and lesson 9.3 inspects the GKE alternative for the model service. The kit deploys the peer to neither.

#### What it costs

Model calls are priced from `shared/prices.py`. rag-api's answer inside `retrieve` costs at most what `config.py`'s budget allows one answer: 8,000 tokens in and 2,048 out at gemini-3.6-flash's list price, Rs 2.33. The peer's own calls, about two a question by the kit's own count, are printed by each question in tokens and rupees. Agent Engine's own charges are not stated by the kit (fact 12).

Each point is checked in the kit's code, or in the pinned google-adk, and the build asserts it, so this box changes when they do.

- No card, so no A2A. `SELF_URL` stays behind and nothing serves a card. The managed peer answers the query API alone.

- The door is the whole project's. Nothing in the kit sets a policy on the instance. `up` prints who may query it, and fact 8 says whether a policy could narrow that.

- The user id is the caller's word. Sessions are filed under the `user_id` in the request, and the API's own read names no user (fact 9).

- One identity for two hosts. `documind-mcp`'s rows cannot tell the hosts apart. The plan leaves the managed peer's own account for after 6 December (its section 10).

- google-cloud-aiplatform is unpinned by default. ADK's deploy appends it with no version, so the image takes the latest; the wrapper's line records which one (fact 11).

- Two settings wait on a lane run. `MANAGED_PEER_GRANT_ROLE` defaults to the role the author's probe grants when its deploy is refused (fact 2). The runtime log's resource type, which `trace` and the smoke's eighth check read, is unverified, so that check is a SKIP when the line is not found.

- Out of the cohort's scope. The plan's section 10 leaves for after 6 December the managed peer's own account, `adk web`, and managed sessions and Memory Bank.

### Tear it down, and verify it yourself

Nothing left billing, read back; then the checklist.

#### Definition

`make managed-peer-down` deletes the instance by name, and every other `documind-managed-peer` instance in the region, with `force=True` so their sessions go with them. It reads each one back until the API says it is gone, for up to a minute, and takes back the grant `up` added, and only that. Each step stands alone, so one failure never hides another. Anything left is printed with the command that deletes it, and the exit code is 4. Run it twice: the second run finds nothing to delete.

#### The code

#### Do it

The first run deleted the instance, read it back gone and took back the grant. The second listed the region, found no `documind-managed-peer` instance, and said so. The records in `runs.ndjson` stay on your machine for `compare`; `down` removes only the state file that named the instance.

#### Verify it yourself: the checklist

Nothing that bills. Step 6 made an instance and a grant; step 10 deleted the one and took back the other, and the second run read the region back empty. The Cloud Run peer and `documind-mcp` are as they were, and their logs keep the rows your questions wrote. On your machine stay `~/managed-peer-venv`, `~/peer-pins-venv` and `/tmp/mp109`, which you may delete, and the records in `evals/reports/managed-peer/runs.ndjson`. Lesson 10.10 turns to coding agents: a Ralph loop, an AI code reviewer, and paper-to-code.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.9 Run the peer on Google's managed agent platform · v5.0

Next: Lesson 10.10 Coding agents: a Ralph loop, an AI code reviewer and paper-to-code.
