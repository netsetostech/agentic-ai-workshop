# Lesson 10.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.7_A2A_Handoff_WIX.html`, reviewed at blob `687e6663142d3602ab105d211e0fa11b3981a1f8`. Learners read that page on the course site; this guide keeps its prose.

The ADK brain answers from the documents with two tools. The A2A peer that lesson 10.6 traced holds the inventory tools: which documents the corpus holds, and how many. This lesson gives the ADK brain a third tool, `documind_peer`, that hands one question to the peer. It is off unless `PEER_URL` is set. Only the question crosses. Before anything is sent, a gate refuses a third hand-off in a turn, and a confused deputy: a peer that would answer from another tenant's documents. A hand-off waits at most 75 s, and the peer stops each task at 12 model calls. Then loops and deadlocks. A cycle among the lane's own services is refused by construction, when you check the caller graph. A loop through an agent the lane does not run is refused at run time, before the peer makes a single model call.

- One question across, a cap on the far side, and no way back

- The words: hand-off, gate, confused deputy, budget, cap, caller graph, cycle, chain

- Before you run anything: set up the shell

- Switch the hand-off on, and ask the ADK brain

- The hand-off in the kit: what crosses, and the gate in front of it

- The far side: the peer stops a task at 12 model calls

- The hand-off over REST: the response, the smoke, and the confused deputy

- What the lane logs: the hand-off line beside the chat row

- A loop among the lane's own services: refused by construction

- A loop through someone else's agent: refused at run time

- Why it is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what crosses when the ADK brain hands a question to the peer, what refuses a hand-off before it is sent, and what bounds one that is sent. Then you will prove it: `documind_peer` in the turn's `tool_calls` with the peer's task completed, a cycle refused by construction, and a loop refused at run time before any model call.

### One question across, a cap on the far side, and no way back

What crosses, what refuses, what bounds, and why a loop between services is a deadlock.

Why hand a question over. The ADK brain has two tools, `retrieve` and `calculate_processing_cost`. They answer what a document says and what processing costs. Neither can say which documents the corpus holds: that is `list_documents` and `corpus_stats` on `documind-mcp`, and the peer from lesson 10.6 holds them. `documind_peer` is one more tool, for the ADK brain alone. It hands the peer one question and brings back the peer's answer, in words, with no passages to cite. It exists only while `PEER_URL` is set on the chat service, and `make handoff` sets it.

Only the question crosses. A hand-off is one A2A message. It carries the question's words. Beside them, in the request's metadata, go the delegation chain, `["documind_adk"]`, and a random hand-off id. The tenant, the person and the thread stay behind. The chat calls the peer as its own account, `documind-chat-sa`, one of the two invokers lesson 10.6 showed. The peer reads the corpus as its own account, `documind-agent-sa`, which sits on acme's roster alone.

A confused deputy, refused before anything is sent. That last fact is a trap. A zeta member asks the chat, the chat asks the peer, and the peer answers from acme's corpus. A service that holds more access than the person it acts for, and uses it for them, is a confused deputy. So before each hand-off, `peer.py` reads every roster the peer's account is on, and sends only when that is exactly one roster, the asker's. The refusal names no tenant. The asker learns only that the peer's corpus is not theirs.

Three limits, two near and one far. A turn may hand off at most 2 questions. A third is refused before it is sent, and calls the model makes side by side count each other. One hand-off waits at most 75 s, and never past the turn's own deadline of 100 s from lesson 5.5. The UI waits 120 s for the whole turn. A cut hand-off is data for the model, as a cut search is. On the far side, the peer stops each task at 12 model calls. Before this lesson's kit it ran under ADK's default of 500.

Loops and deadlocks. Each service holds a request while it waits on the service it called, and each has a fixed number of slots. The chat takes 20 requests at a time on each of at most 10 instances, and the peer 20 on each of at most 5. If the peer could call the chat back, a hand-off could come back to a chat that is waiting on it. Under load, each side fills its slots with requests waiting on the other, and only timeouts end it. That is a deadlock across services.

Refused twice: by construction, and at run time. An account may invoke a service only where that service's deploy script binds it. `make check-callers GRAPH=1` reads those bindings and shows they hold no cycle, so the lane's own services cannot deadlock this way. It cannot see an agent the lane does not run, such as a partner's agent that asks the peer again. For that the request carries its own chain. With `PEER_CHAIN=on`, the peer refuses a request whose chain already names it, or that would be a third hop, before its first model call.

A hospital ward and an outside lab. The ward may send a requisition slip to an empanelled lab. The slip names the test and nothing else: not the patient's file, not the ward's notes. The lab works under its own registration, which covers one hospital. So the ward never sends a slip for a patient of another hospital, and the refusal does not say whose registration it is. A visit gets at most two slips. The doctor waits a fixed time for each result and then carries on without it, and the lab stops any test that runs past its own limit. Two rules keep slips from going round in circles. The contracts say who may send slips to whom, and nobody signs a set in which a slip can come back to the desk that sent it. And every slip lists the desks it has passed: a desk that finds its own name there, or two desks already listed, sends it back unrun.

#### Follow one hand-off

Choose who asks, what the chat's model sends, and how the peer behaves. The panel follows the turn through the gate, the peer's door, the peer, and back to the model.

Each of the 24 outcomes is what the kit's code did when this page was built: the kit's chat app and its ADK brain, `peer.py` and a2a-sdk's client, against the kit's own peer. Gemini was scripted on both sides, and the rosters, the tokens and Cloud Run's check were stood in. For the slow peer the build set `PEER_TIMEOUT_S` to 2 s; on your lane it is 75 s.

#### Try to close a loop

On the left, add one invoker binding to a deploy script and see what `check-callers` says. On the right, send the peer a request that has come along a chain, with its switch off and on.

The left is `commands/check_callers.py` run on copies of the kit's `sa.tf` and deploy scripts, each with that one line changed. The right is the kit's peer, served offline with its model scripted and counted, at `PEER_CHAIN=off` and `on`.

On your lane, Gemini decides whether a question goes to the peer, and writes both answers. The gate, the limits, the caller graph and the chain are the kit's, and they do not change.

### The words: hand-off, gate, confused deputy, budget, cap, caller graph, cycle, chain

Fifteen rows, each with the value it takes on your lane.

One distinction to hold. The gate refuses a hand-off before it leaves the chat. The budget, the cap and the chain bound a request that has left. The caller graph is checked before anything runs at all.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `tok`. The peer and the chat must run this lesson's kit: the peer's image with its cap, and the chat's with `peer.py` and a2a-sdk. If the peer's `/health` in step 5 names no `max_llm_calls`, or the chat was deployed before your last `git pull`, build and deploy them again with this cell. Otherwise skip it.

What changes on your lane: step 3 switches the hand-off on and step 7 switches it off. Step 5's drill caps the peer at 1 for a minute or two, then puts 12 back. Step 6 swaps `PEER_ACCOUNT` for one cell and puts it back. Step 9 deploys the peer with `PEER_CHAIN=on`, which stays until its next deploy. The model calls of steps 3, 5 and 6 cost a few rupees in all.

### Switch the hand-off on, and ask the ADK brain

One env update on the chat, then two questions in the UI.

#### Definition

`make handoff` checks three things on Cloud Run before it changes anything: that the chat's latest revision takes all the traffic, since an env update makes a new revision that must serve; that `documind-agent` is deployed, and which account it runs as; and that `documind-chat-sa` may invoke it. Then it sets `PEER_URL` and `PEER_ACCOUNT` on `documind-chat` in one env update. That makes a new revision; nothing is rebuilt and no model is called. `PEER_ACCOUNT` is read from Cloud Run, never typed, so the gate checks the rosters of the account that really answers. The first line of the cell notes the time, for step 7's logs, and the two services' addresses.

#### Do it

#### Then, in the UI

Open the UI at `https://documind-ui-NUMBER.asia-south1.run.app`, signed in as yourself; Module 0 put your account on acme's roster. Choose the `adk` brain in the sidebar and ask two questions: Which documents does the corpus hold, and how many are there?, then Which documents does the corpus hold, and after how many years of continuous service does gratuity become payable?. Under each answer, the caption names the tools the turn called.

The caption is the response's `tool_calls`. For the first question it names `documind_peer` alone: the model chose the tool from its description, which names what the corpus holds and how many documents there are, and the brain's own two tools cover neither. For the second it names `documind_peer` and `retrieve`: one question went to the peer and one search ran beside it. Each answer came from two models, the chat's, which chose the tools, and the peer's, which answered inside its own A2A task.

The hand-off stays on until step 7's `make handoff OFF=1`, or until the chat's next deploy, which sets every variable afresh.

### The hand-off in the kit: what crosses, and the gate in front of it

One file holds the tool; the ADK brain adds it in two lines and keeps its record in two more.

#### Definition

`services/chat/peer.py` is the whole hand-off: the description the model reads, the gate, the wait, the message, and the record. `documind_peer` records each call before its first `await`, so calls the model makes side by side count each other. It reads the peer account's rosters as each hand-off starts, so a roster change counts at once. It sends with the chat's own ID token, minted for the peer's address, and waits at most the budget `budget_s()` gives it. Every failure comes back as data the model reads: a refusal, a task that ended `failed`, a cut hand-off, a door that would not open. `brains.py` adds the tool only while `PEER_URL` is set, and only to the ADK brain.

#### The code

#### Do it: the gate and the wait, on the kit's own code

No network and no model: the cell imports `peer.py`, asks its gate about four askers, then asks how long a hand-off may wait with 100 s, 30 s and half a second left in the turn.

One asker of four was sent. The cap per turn comes first, so a third hand-off is refused whoever asks. Then the rosters: the peer's account must sit on exactly one roster, and it must be the asker's. A zeta member fails that, and so does an acme member when the peer's account sits on three rosters, because its answer could then come from any of them. The wait is the smaller of 75 s and the time the turn has left, and never under the 1 s floor every tool call gets.

#### What the build ran: the hand-off, end to end

When this page was built, the kit's chat app took 25 turns through the desk's door and the ADK brain, and `peer.py` sent through a2a-sdk's client to the kit's own peer, whose door noted what reached it. Four of those turns are below; step 1's first panel holds the rest.

The first turn has the proof's shape: `documind_peer` in `tool_calls`, and the peer's task `completed`. What reached the peer was the card request and one message, both as `documind-chat-sa`. The message held the question's words, and its metadata held the chain and the hand-off id, the same id as the hand-off's log line. The zeta member's question never left the chat, and the third of three was refused before it was sent. The log line counted the question's characters, and the chat row kept its keys.

### The far side: the peer stops a task at 12 model calls

A looping peer ends its task `failed`, and the turn reads that as data.

#### Definition

The budget bounds how long the chat waits. It does not bound the peer, whose model could keep working long after the chat stopped waiting. ADK reads `ADK_MAX_LLM_CALLS` as each task starts, raises `LlmCallsLimitExceededError` on the call over the cap, and `to_a2a` ends the task `failed`. `agent.py` sets 12 unless the environment already says otherwise, and its `/health` reports it. `make agent-drill` proves it on your lane. It sets the cap to 1, sends `make smoke-agent`'s first task and expects `failed`. Then it puts the cap back from a trap and sends the task again, which must complete.

#### The code

#### Do it: the cap, published

#### What the build ran: a loop stopped at 12

#### Do it: trip the cap on your lane

The scripted loop asked for its tool 12 times and was stopped on the next call: the task ended `TASK_STATE_FAILED` with the limit in its status message. Sent through the hand-off, that comes back to the chat's model as `the peer's task ended failed`, and the record's outcome is `failed`. On your lane the drill did the same at a cap of 1: the task's first model call asked for `retrieve`, and the next was never made. With the cap put back, the same task completed with its answer. The two tasks took 3 model calls in all.

### The hand-off over REST: the response, the smoke, and the confused deputy

Two turns through `/v1/chat`, then a third with the peer's account on three rosters.

#### Definition

`make smoke-handoff` is the hand-off's live check, in two turns as `documind-ui-sa`, which resolves to acme. Check 1 asks the ADK brain the smoke's question and wants HTTP 200, `documind_peer` among the tool calls, a hand-off in the response's `handoffs`: answered, the peer's task completed, within its budget; and an answer that is not empty. Check 2 asks the LangChain brain the same question and wants no `handoffs` key: the ADK brain alone hands off.

The deputy cell sets `PEER_ACCOUNT` to `documind-ui-sa`, which sits on three rosters, and asks the ADK brain the smoke's question, Ask DocuMind's A2A peer which documents the corpus holds, and how many there are. It prints the record, then puts `PEER_ACCOUNT` back with `make handoff`.

#### Do it: the smoke

#### Do it: a confused deputy

Two passes. The first is the proof on your lane: `documind_peer` in `tool_calls`, and the peer's task `completed` inside its budget. The second shows the switch is the ADK brain's alone. In the deputy cell the model asked for the peer, and the gate refused before a message was sent: the record's outcome is `refused`, its budget is `None` because nothing waited, and its reason names no tenant. The refusal is in `refusals`, as a blocked tool's is, and the turn still answered 200.

### What the lane logs: the hand-off line beside the chat row

One line per hand-off, sent or refused, joined to its turn by tenant, user and time.

#### Definition

Each hand-off writes one log line, `{"event": "handoff", ...}`, from `peer.py`'s `finally` block, so a refusal, a failure and a cut are logged as surely as an answer. The line names the tenant, the user, the outcome, the seconds against the budget, and how many rosters the peer's account is on, never their names. It carries the hand-off id that also went to the peer. The question's words are not there, only their length, as the chat row keeps tool names and never their arguments. The chat row keeps its own keys: lesson 11.5 reads them, so the record went into the response and this line instead.

#### The code

#### Do it

One hand-off line for each hand-off since step 3: your two UI turns, the smoke's turn, and the deputy cell's refusal, the only one with three rosters. Each sent hand-off's seconds sit inside its 75 s budget. Beside them, the ADK brain's chat rows name `documind_peer` in their tools, and none has a `handoffs` key. To find what a hand-off asked, you read the response; to find that it happened and how it ended, you read this line.

#### Then switch the hand-off off

### A loop among the lane's own services: refused by construction

The caller graph, read from the deploy scripts, and one edge back that fails it.

#### Definition

Who may invoke a Cloud Run service is that service's own IAM binding, `roles/run.invoker`, made by the script that deploys it. `terraform/sa.tf` names the services on the request path and the script for each. `check_callers.py` reads each script as it stands: the account its `gcloud run deploy` runs the service as, and the accounts its invoker bindings name, with a `for` loop expanded. Wherever one service's account may invoke another service, that is an edge. Then it walks the graph. It prints `acyclic` and an order in which every service calls only services after it, or the first cycle it meets, and exits 1. It reads files only: no gcloud, no credential.

#### The code

#### Do it

6 services and 9 edges, and no cycle: `documind-ui, documind-gchat, documind-chat, documind-agent, documind-mcp, documind-api`. The chat may call the peer, and nothing the peer runs as may call the chat. The eval accounts, the outsider, the Chat push account and Google's two service agents may call services but run none, so nothing calls them and they close no loop. The kit's own CI runs `commands/tests/test_check_callers.py`, which holds this graph acyclic, so a back edge fails a pull request before anything is deployed.

#### Change it: an edge back from the peer to the chat

This loop in `lesson-12.8.sh` binds who may invoke `documind-chat`. Add `documind-agent-sa` to it, as an edit meant to let the peer ask the chat something would, then run the check, then put the file back.

One added name made a tenth edge, `documind-agent -> documind-chat`, and with it the cycle `documind-chat -> documind-agent -> documind-chat`. The check exits 1, so a pipeline that runs it stops there. That is the deadlock from step 1, refused before it could be deployed: under load, the chat's slots and the peer's would fill with requests waiting on each other. With the file put back, the graph is acyclic again.

### A loop through someone else's agent: refused at run time

The request carries its chain, and the peer reads it before its first model call.

#### Definition

The caller graph sees only what the lane deploys. A partner's agent that the peer answers could hand the question on to an agent that asks the peer again. Every hop is a new task, every task may spend 12 model calls, and nothing but a timeout ends the loop. So the request carries its own chain in its metadata, because A2A 1.0 has no standard field for one: `documind_chain`, the agents that handed it on in order, and `documind_handoff_id`. The chat sends `["documind_adk"]`. With `PEER_CHAIN=on`, `agent.py` hands `to_a2a` the factory in `chain.py`: ADK's own executor, with one check in front. A chain that already names the peer is a loop, and one that holds 3 agents would make a third hop. Both are refused before the runner starts, so they cost no model call. The refusal is a task, ended as ADK ends one: `TASK_STATE_REJECTED`, with the reason in its status message. Off, `agent.py` never imports `chain.py`.

#### The code

#### What the build ran: five chains, off and on

#### Do it: switch it on, then send two chained tasks

The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's `/health`, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

Both tasks came back `rejected`, the A2A 0.3 wire's name for `TASK_STATE_REJECTED`, and each history holds the question alone: the peer's model never ran. The first chain already named `documind_peer`; the second held 3 agents. In the build's run, the same requests with the switch off ran to completion, two model calls each, and the chat's own chain was answered with the switch on. The peer logged one `a2a_refused` line for each refusal, with the reason, the chain's length and the hand-off id, and no words and no names.

### Why it is built this way, what it costs, and what the kit does not do yet

The design choices, every guard as a constant you can find, a ping-pong ended by a cap, then the bill and the gaps.

- Only the question crosses. The peer has its own account and its own roster, so it needs nothing about the asker, and nothing personal goes into the message or its metadata.

- The gate runs before the send. A refused hand-off costs no token mint, no request and no peer model call, and it reads the rosters each time, so a roster change counts at once.

- Every failure is data. A refusal, a failed task, a cut hand-off and a shut door each return a value the model reads, and the turn still answers 200, as a failed search does. A roster that cannot be read, or a token that cannot be minted, still fails the turn, as a failed mint does in lesson 5.5.

- The record lives in the response and one log line. The chat row's keys are what lesson 11.5 reads, so they stay as they are.

- Two kinds of loop, two guards. The lane's own services are checked from the deploy scripts before anything runs. An agent the lane does not run can only be met at run time, so the request carries the evidence.

#### Every guard, and where it lives

#### A ping-pong, and the cap that ends it

Every guard above sits on the lane. One more loop needs neither a hand-off nor a second service: two agents that may each hand the turn to the other, where neither owns the answer. In ADK it is one setting away. An agent under a parent is offered `transfer_to_agent`, whose `agent_name` is an enum of the agents it may reach: its parent, and its peers unless `disallow_transfer_to_peers` is set. `commands/agent_shapes.py` builds two such desks under a root, scripts each to want the other desk to answer, and puts one plugin on the run, `TransferCap`. It counts the agents a turn starts in a `temp:` key, which ADK keeps for one turn and never stores, and once 3 transfers have been made it answers in place of the next agent, before that agent's model is called.

Run it offline, at Rs 0. It runs the same turn twice, with the peer edges and without them:

Three things to read in it. The enum is the graph of allowed hand-offs, and the desks only follow it. The cap, not the desks, ends each turn: the fourth transfer is refused before the agent it names runs, so a turn makes 4 model calls and no more. And taking the peer edges away does not end the loop: each desk is offered only the root, the question goes round through the root, and the same cap ends it. Fewer edges still left a cycle; only the count stopped it. This cap lives in a command, not on the lane: no agent the kit deploys transfers to another.

#### What it costs

Each point is read from the kit's code, and the page's build asserts it, so this box cannot outlive the kit it describes.

- The chain binds only agents that forward it. A partner that drops the metadata starts a fresh chain. What bounds it then are the local limits: 2 hand-offs a turn on the chat, 12 model calls a task on the peer.

- `check-callers` reads the scripts, not the lane. `GRAPH=1` is its only mode. A binding added by hand on Cloud Run is not in any script, so the check cannot see it.

- A cut hand-off is not cancelled at the peer. The chat stops waiting, but the peer's task runs on, up to its 12 calls, and those calls are billed. No deadline travels with the request.

- The peer's answer carries no citations. It comes back in words, and the turn's citations are only its own searches.

- The ADK brain alone hands off. The LangChain, LangGraph and direct brains never see the tool.

- The hand-off is not on the chat row. Whatever reads the chat row, lesson 11.5's reports included, does not see a hand-off. You join the hand-off line to its turn by tenant, user and time.

- `smoke-handoff` is in no gate. The hand-off is off by default, so no gate runs its smoke.

- The next deploy switches it off. `lesson-12.8.sh` sets every variable on `documind-chat`, and `PEER_URL` is not among them.

- The response keeps the question's words. `handoffs[].request` holds what crossed; only the log line is reduced to a length.

- The transfer cap is offline only. `agent_shapes.py` runs on scripted models, `OFFLINE=1` being its only mode, and no agent the kit deploys transfers to another, so nothing on the lane carries the cap. Whether Gemini itself would pass a question back and forth is not shown.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it on your lane.

The peer and the chat run this lesson's kit, and the peer's cap of 12 stays: it is the kit's default now. The hand-off was on from step 3 to step 7; if you skipped step 7, it stays on until `make handoff OFF=1` or the chat's next deploy. The peer runs with `PEER_CHAIN=on` until its next deploy. The drill and the deputy cell put back what they changed. Lesson 10.8 attacks these agents with an injected document and a poisoned tool, and measures what holds.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.7 Hand one question to the A2A peer, and stop loops and deadlocks · v5.0

Next: Lesson 10.8 Defend agents against injected documents and poisoned tools.
