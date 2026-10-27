# Lesson 5.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.8_Human_In_Loop_WIX.html`, reviewed at blob `e4f5251946e9173b1c0555451a11ffdeaa9dec61`. Learners read that page on the course site; this guide keeps its prose.

Some steps in an agent's turn belong to a person. Withdrawing a company document needs a second person's approval, and the person who asked can never be that second person. A question that lacks one fact needs the asker's answer, and nobody else's. A request for a person needs a person. The kit's `services/chat/approval.py` pauses a LangGraph turn for each of these: the turn stops inside a node, the checkpointer keeps it, and a decision resumes it, even from another process. You run it offline first, at Rs 0. On your lane you use the hand-off lesson 5.6 built: you give yourself the People team's role, ask for a person on the Desk page and over REST, and read the case in the People team's inbox. Then you watch a question that lacks a fact get its answer on the same thread. Last, behind a company switch that is off until you set it, the same pause runs on your lane: a withdrawal waits as an approval record, a second person holding `doc_approver` decides it over REST, and you run the approved withdrawal from your shell.

- Four ways a person comes into a turn

- The words: interrupt, resume, paused turn, decision, four eyes, requester, ask_user, offer_case, case_offer, people_ops

- Before you run anything: set up the shell

- Your lane: the People team's reader, and a request for a person on the Desk page

- The pause, in the kit: approval.py

- Pause, refuse, approve and resume on your machine

- Escalate and clarify over REST, on your lane

- The rows, the case and your role, read directly

- The approval wired in: a withdrawal paused on your lane, decided over REST, run by you

- Why it is shaped this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how a LangGraph turn waits for a person: `interrupt()` in an approve node, the checkpointer keeping the paused turn, and a decision that resumes it, with three locks that stop the person who asked from approving their own withdrawal. Then you will prove it. Offline, a withdrawal is paused, refused to the person who asked, approved by a second person and resumed by another process, and a clarifying question is answered by the person who asked. On your lane, a request for a person reaches the People team's inbox. Then, behind a company switch that is off until you set it, the same pause runs on your lane: a withdrawal paused as an approval record, held, refused to the person who asked, approved by a second person over REST, run by you from the shell, and undone.

### Four ways a person comes into a turn

A turn that waits, four eyes on a withdrawal, a question only the asker answers, and a hand-off to the person the law names.

A turn can wait. Until now, every turn on the chat service ran from question to answer inside one request: the model asked for tools, the tools ran, the model answered. LangGraph can stop a turn halfway. A node calls `interrupt()` with a payload, and the run stops there. The checkpointer keeps everything: the thread's messages, the calls still waiting, and the payload. Nothing more runs until someone resumes the thread with `Command(resume=...)`. That can be another request, another process or the next day, as long as it reads the same checkpointer. The node then runs again from its first line, and this time `interrupt()` returns the value sent. So nothing above `interrupt()` in that node may have a side effect: it runs once at the pause and again at the resume.

Approve: four eyes. `approval.py` gives the model a tool with a side effect. `withdraw_document` takes one of the company's documents out of search, so that no answer cites it. Withdrawn is not deleted: `make restore` brings the document back. The approve node pauses the turn before the tool can run, and waits for a second person in the company. The person who asked may reject their own request, which cancels it, but cannot approve it. Who asked is read from the thread id, `tenant:user:session`, which `agent.py` builds from the verified caller, never from the model, a request body or the resume. Three locks check this. `decide()` checks it before anything runs. The approve node checks it again on the value the resume brings. The tool checks it last: it runs only when the resumed turn names a second person's approval of this exact call.

Clarify: a question only the asker answers. `ask_user` pauses the turn too, but for the person who asked, and only for them. Their answer comes back as the tool's result, a "respond" decision, so the model reads it within the same turn. Until a company's switch is on (step 8), your lane has no such tool. The brains hold `retrieve` and `calculate_processing_cost`, so a model that lacks a fact can only put its question in its answer and end the turn. Your reply is then a new turn, and only the thread connects it to the question.

Escalate: hand it to the person the law names. Lesson 5.6's chat door already does this on your lane, by rule, before any brain runs. A request for a person gets a fixed reply and `case_offer`, and the person presses the button and confirms. The case then waits in the People team's queue, for whoever holds `people_ops`. `offer_case` lets a model make the same offer when the rules miss. It checks the person's roles and the company's queue, and writes nothing: the person still raises the case. It runs offline, like the rest of `approval.py`, and on your lane once a company's switch is on.

Offline first, wired in behind a switch. One module in the chat service imports `approval.py`: `approval_routes.py`, and it does something only for a company whose `tenant_settings.agent_actions` is `approval`. No company's is until an operator writes it, with `make agent-actions`. For every other company, and for the LangChain, ADK and direct brains, the chat service on your lane is what it was: `tools.BLOCKED` and the LangGraph brain's refuse node stay as lessons 5.4, 5.5 and 5.7 show them. For a company that is on, the LangGraph brain is the graph with the approve node, the pause is a record in Firestore (`shared/approvals.py`), a paused conversation takes no new question, and three routes under `/v1/approvals` list, read and decide the records. Steps 4 and 5 prove the pause offline, on a scripted model, at Rs 0. Step 8 switches acme on, runs the whole flow on your lane, and switches it off again.

The government file again, with a checker. Lesson 5.4's file moved from officer to officer. Some notings cannot be signed by the officer who wrote them: maker and checker are two people. A clerk who drafts an order to weed out a record cannot approve it. The file waits in the checker's in-tray, flagged at the page. Nobody re-types it: next morning the checker opens it at the flag, signs it or returns it with a reason, and it moves on from exactly there. A noting that needs a fact from the applicant goes back to them as a query, and only the applicant's reply is filed against it. A matter the rules give to a committee is referred to it with a note on the file, and the desk does not decide it. The in-tray is the checkpointer, and the flag is `interrupt()`. Maker and checker are four eyes. The query is `ask_user`, and the referral is the case.

#### Step through a paused turn

Choose what the model asks for, then send a decision as Asha (`asha@example.com`), who asked, or as Ravi or Meena, two other people. Try Asha approving her own withdrawal, Ravi answering Asha's question, a decision sent straight to the graph without `decide()`, and a second decision after the turn has ended. Each result is the kit's own: the page's build ran all 81 decisions through `approval.py`. Without `may_approve`, `decide()` lets anyone but the person who asked approve; the second choice under "How it arrives" passes one that allows Ravi alone.

The build ran each scenario to its pause with `build_approval_graph()` from your kit, a scripted model and an in-memory checkpointer. It then ran every person's decision on a fresh copy of that pause, through `decide()`, through `decide()` with a `may_approve` that allows Ravi alone, and straight into the graph with `Command(resume=...)`. After every refusal it checked with `paused()` that the same calls still wait. The people, the document and the fake roster are the ones the kit's own tests use (`commands/tests/test_approvals.py`). The panel looks the results up; it decides nothing itself.

The model's messages are scripted, and its last answer is not shown, only what the kit did. The executor that would withdraw records the call and withdraws nothing, and the search is a stand-in. On your lane no turn pauses. Step 6 does the escalation and the clarification for real.

### The words: interrupt, resume, paused turn, decision, four eyes, requester, ask_user, offer_case, case_offer, people_ops, agent_actions, approval record, doc_approver

Twenty-two rows, each with where it lives in the kit, or on your lane.

One distinction to hold: approve and respond both resume a paused turn, but they come from different people. A withdrawal waits for anyone except the person who asked. A question waits for that person alone.

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

You need the shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `ME`, and the chat service lesson 5.1 deployed. You also need what lesson 5.6 left on your lane: acme's queues, the eval accounts on their rosters, and your four roles. Step 3 changes your lane: it adds `people_ops` to your roles, and you raise one case on the Desk page. Steps 4 and 5 make or complete `~/graph-venv` with the chat image's pins and the SQLite checkpointer, and touch nothing on your lane. Step 6 asks the chat service five questions as `documind-evalacme-sa`, and raises and withdraws one case. Step 8 changes your lane more, and undoes most of it: it switches acme's `agent_actions` to `approval`, gives `documind-evalacme-sa` the `doc_approver` role, withdraws one small document and brings it back, then switches acme off again; the approval records and their audit events stay. Run steps 3, 6, 7 and 8 in the same shell, in order: step 3 defines `CHAT`, `SINCE108`, `sa` and `etok`, and the later steps use them.

### Your lane: the People team's reader, and a request for a person on the Desk page

The People team's role for you, then a request for a person told to the Desk, sent as a case, and read in the People team's inbox.

#### Do it: the People team's reader

A request for a person goes to acme's `people` queue, the People team's. A case there is read by whoever holds `people_ops`, and nobody on your lane holds it yet: lesson 5.6 gave you the roles that read grievances and POSH cases. So far a request for a person would reach no one. The cell sets the names the later steps use, notes the time in `SINCE108` for step 7's log read, and gives you `people_ops` beside the four roles you have. `ROLES=` sets exactly the roles it lists, so it names all five.

`make roles` wrote your role document. `before` lists the four roles lesson 5.6 gave you, `granted` names `people_ops` alone, and `revoked` is empty. The grant is one `role.grant` event in the audit bucket. Roles are read on every request, so the Desk page shows you the People team's inbox at once.

#### Do it: ask for a person on the Desk page

- Tell the Desk. Open the UI, sign in as yourself and choose Desk. In the Tell the Desk box, "What do you need help with?", type `Escalate this to a human please` and press Send. The sentence is one of the gate's own `human_requested` examples, from `commands/tests/test_desk_rules.py`. The reply is the fixed text: "You asked for a person. DocuMind does not answer this itself: it did not search its documents for this or write an answer to it. DocuMind does not pass this to a person by itself. Contact the People team directly, or raise a case for them where your company's DocuMind offers it." Under it is the caption "This is a fixed reply. No AI model was used. To reach a person, raise the case below. A case does not include what you typed here." and a button, Ask for a person.

- Send the case. Press Ask for a person. Under Raise a case, "What is it about?" now reads "I want to talk to a person", and the form is empty. Write a sentence of your own in "In your own words (you can change this before sending)" and press Next: check it before sending. The draft reads "Asked for a person: not sent yet" and "Goes to: People team", with the contact acme's queues file names, and below the form, "Nothing is sent until you press Send. This draft is kept for 30 minutes". Press Send. The page says "Sent. Your case reference is", then eight characters, and that you can follow it under Your cases.

- Read it as the People team. Under Your inbox the case shows as "Asked for a person", with "Status: Sent", who raised it and your words under "In their words:". In "Change the status to", choose "Acknowledged (we have seen it)" and press Update. Under Your cases, "Asked for a person" now shows "Status: Seen by the team".

The Desk page sent your words to `POST /v1/chat`, and the chat door answered before any brain ran. It found the class `human_requested`, sent the fixed reply, and named the class in `case_offer`. The button came from `case_offer`, never from your words, and the form started empty. The draft and the send went through the case routes as you. The case went to the `people` queue, and the inbox showed it to you because you now hold `people_ops`. `human_requested` is not one of the sensitive classes, so the door's log row names you as well as the class; step 7 reads it. The Chat page would have shown the same fixed reply, with "brain: desk_gate" in its caption, but no button: it does not read `case_offer`.

That is the escalation the kit runs on your lane: by rule, at the door, and raised by the person. You were the person who asked and the People team at once, so one sign-in shows both sides; on a real lane they are different people.

### The pause, in the kit: approval.py

Three tools that bring a person into a turn, who may decide what, the approve node, and the kit's own tests.

#### Definition

`services/chat/approval.py` is 400 lines. Its docstring opens with the fact the rest depends on: one module in the service imports it, `approval_routes.py`, behind a company's switch that is off until an operator sets it. The build checks that too: no other file under `services/` imports it, `tools.BLOCKED` still holds its three names, and the LangGraph brain still has its refuse node.

#### The three tools

`NEEDS_APPROVAL`, `NEEDS_ANSWER` and `DECISIONS` say who ends which pause. A document's name is at most 200 characters, a reason for a rejection at most 200, and an answer at most 4,000. `CaseType` lists the six kinds the Desk page's button offers.

The person who asked is never a tool argument. `owner()` reads them from the thread id, which the server builds from the verified caller, so neither the model nor a resume can change it.

`withdraw_document` takes its tenant and the person who asked from the thread. It accepts a bare file name, `tenant/name` or the upload URI, and refuses another tenant's document or a path. Then comes the last lock: the resumed turn's context must name someone other than the person who asked as the approver of this call's id. What withdraws is injected, and the result names the undo.

`ask_user`'s body runs only where nobody was asked, and it tells the model to put the question in its answer. That is what happens on your lane while a company's switch is off, where the brain has no such tool.

`offer_case` checks that the person's roles open the case desk and that the company has a queue for the kind of case, as `GET /v1/cases/offer` decides it. It takes no reason, so nothing a person disclosed reaches its result, and it writes nothing: its `case_offer` has the chat door's key and shape.

#### Who may decide

`_check()` holds the rules. `approve` may come from anyone but the person who asked, and, when `may_approve` is given, only from someone it allows. `reject` may come from the person who asked, as their cancel, or from a second person. `respond` may come only from the person who asked. A decision with no person named, the wrong kind for the tool, a reason that is too long or an empty answer is refused too.

#### The approve node

`route()` sends a turn with any call that needs a person to `approve`, where the brain's route sends a blocked call to `refuse`. The approve node builds the pause's payload, in the shape LangChain's middleware uses, and calls `interrupt()`. On the resume it checks the decisions again with `_refusals()`: a resume that breaks a rule gets another `interrupt()`, which says why. Below that come the "approval asked" log line, an error result for each rejected call, and the answer as the result of each question answered. `onward()` then sends every call still without a result to the tools, one `Send` each: the approved calls, and any call asked for beside them. With none, it goes back to `agent`.

The graph is the LangGraph brain's, with `approve` where `refuse` is. It has seven edges to the brain's six: `refuse` only goes back to `agent`, while `approve` can also send calls on to `tools`.

#### decide() and paused()

`paused()` reads the interrupt's payload and checks that it matches the calls waiting in the thread. `decide()` refuses before anything runs. Nothing waiting is a `LookupError`, which a route would answer as 409. A wrong count or kind of decision is a `ValueError`, 422. A person the rules do not allow is a `PermissionError`, 403. Then it resumes the turn. The resumed turn's context takes its tenant and user from the thread, whatever context the caller passes, and names who approved each call, which is what the tool's lock reads.

#### The middleware form

`hitl_middleware()` gives LangChain's `create_agent` the same pause, with the same decisions and descriptions, and `paused()` reads both forms into one record. Its `after_model` hook is a graph node of its own, so each model call writes one more checkpoint. The build counted them on a scripted model: a turn with one model call writes 3 checkpoints without the middleware and 4 with it, and a turn with two writes 5 and 7. That is why the kit's turn limits wrap the model call instead (lesson 5.5).

#### Do it: the kit's own tests

`make approval-check` is `commands/approval-check.sh`. It makes `~/graph-venv` if it is missing (lesson 5.4 made it), installs the chat image's pins and the SQLite checkpointer, `langgraph-checkpoint-sqlite` 3.1.1, the version `services/chat/requirements-local.txt` pins, and runs `commands/tests/test_approvals.py`. CI's chat-pins step runs the same file. It needs no credential, no network after the install, and costs nothing.

All 15 tests passed: four in the `Wiring` class and eleven in the `Approvals` class. The `Wiring` tests need only the standard library. They check that nothing in the service imports the module, and that it writes no audit event, so the list of actions lesson 4.8 counts is unchanged. They check that it was verified against the image's own pins: LangChain 1.4.0, LangGraph 1.2.12 and the SQLite checkpointer 3.1.1. And they check that the make target, its script and CI's chat-pins step all run this file. The `Approvals` tests drive the module on scripted models, a stand-in rag-api and a fake Firestore that records any write. Each is a claim this page makes, and step 5 runs four of them by hand.

### Pause, refuse, approve and resume on your machine

A withdrawal paused and approved, a second process resuming it from a file, a question only the asker answers, and the Change-it.

#### Do it: a withdrawal, paused and approved

The cell builds the kit's approval graph on a scripted model that asks for `withdraw_document`, with an in-memory checkpointer and an executor that only prints. It streams the turn to its pause and lists what waits. Then it tries Asha's own approval, and Ravi's.

The stream shows the agent node, then `__interrupt__`: the approve node stopped the turn before any tool ran. `paused()` lists one call, `c0`, which takes approve or reject, asked by asha. Asha's approval was refused by `decide()` before anything ran, and the same call still waited. Ravi's approval resumed the turn. The approve node ran again from its first line, so its log line was written now, once, at the resume. Then the tool ran with Ravi's approval in the context, and called the executor with the tenant and the person who asked, both from the thread. The path lists the node each checkpoint said would run next: agent, approve (where the turn waited), tools, agent, and the end.

#### Do it: a second process resumes it

The pause is data in the checkpointer, not a request waiting in memory. The first process pauses the turn into a SQLite file, `~/lesson108_threads.db`, through `SqliteSaver`, the local lane's checkpointer, and ends. The second process is a new interpreter: it builds a new graph on the same file, finds the waiting call, and resumes it with Ravi's approval.

Nothing passed between the two processes but the file. Process 1 ended with the turn paused before `approve`. Process 2 found the same waiting call there, and `decide()` resumed it: the approval line was written in process 2, at the resume, and the executor ran once, with `requested_by` asha and `approved_by` ravi. The kit's own test does the same with two processes. Your lane's checkpointer is Postgres on Cloud SQL, shared by every instance of the chat service, so any instance could resume a turn paused there. Nothing pauses there yet.

#### Do it: a question only the asker answers

The same graph, now with a scripted model that asks Asha which rule applies to her. The handbook's NP-03 gives a confirmed employee at grade E3 or above 60 days' notice, and its PB-02 gives 15 days during probation. Ravi tries to answer for her, Asha tries to approve, then Asha answers.

`ask_user` takes a respond decision and nothing else, and only from asha, the user in the thread id. Ravi's answer was refused with a `PermissionError` and Asha's approval with a `ValueError`, both before anything ran. Her answer became `ask_user`'s result, which the model reads in the same turn. The path went from `approve` straight back to `agent`: the tools had nothing to run.

#### Change it: the approval line above interrupt()

A resumed node runs again from its first line. The kit writes its "approval asked" line below `interrupt()`, so it is written once, at the resume. The first cell defines `twice108`, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above `interrupt()`, from line 364 to line 361, and runs `twice108` again. Then it puts the kit's file back with git, so the setup section's `git pull` next time is not refused.

Above `interrupt()`, the line was written at the pause and again at the resume, twice for one approval, while the tool still ran once. A log line written twice does no harm. An email to the approver, a ticket or a payment made there would go out twice, once each time the node runs. So in any node that pauses, everything above `interrupt()` must be safe to run again.

### Escalate and clarify over REST, on your lane

A request for a person and a near miss, the case the door offered, then a question that lacks a fact and the reply that gives it.

#### Definition

Both cells call the chat service as `documind-evalacme-sa`, lesson 5.6's acme employee, with `etok`'s token, and ask for the LangGraph brain. A question the door lets through runs the same graph lesson 5.4 drew. Each turn's answer carries `limits`: its model calls and its rupees, which the cells print.

#### Do it: escalate

The cell sends the gate's own request for a person on one session, then one of its near misses, "How do I contact HR about payroll?", which `gate()` reads as a question about a process and lets through. Then it raises the case the first reply offered and sends it with a token. Last, it withdraws the case as the person who raised it. It keeps the case's id in `~/lesson108_case.txt` for step 7.

The request for a person never reached the graph: brain `desk_gate`, no tool call, no model call, Rs 0, the fixed reply, and `case_offer` naming `human_requested`. The near miss did reach it. The LangGraph brain searched and answered from the documents, with its own model calls and rupees and no `case_offer`. With acme's switch off, nothing on your lane lets a model offer a case when the rules miss: `offer_case` is bound only behind it (step 8). The case went to the `people` queue, the People team, as a draft that would expire after 30 minutes. Once sent, it was due 5 days after it opened: the company's own target, from acme's queues file. `desk_law` names no legal clock for a request for a person, so that date is the company's alone. The person who raised it then withdrew it. It stays on record as withdrawn, no longer one of the People team's open cases, with a `case.close` event that says the requester withdrew it.

#### Do it: clarify

Three turns. The handbook answers "What is my notice period?" two ways: 60 days for a confirmed employee at grade E3 or above (NP-03), and 15 days during probation (PB-02). The second turn gives, on the same session, the fact the first lacked. The third sends the same reply in a new session.

No turn paused, because with acme's switch off your lane has no `ask_user`: the model could only answer. Read the first answer. Either the model asked which rule applies to you, or it gave both, each with its citation. Either way the turn ended, and nothing marks it as waiting. The second turn ran on the same thread, so the model read its first question and answer before your reply, and could answer for probation. The third turn sent the same words with no thread behind them: the model had only "I am still on probation." to go on. That is clarification on your lane: a question in an answer, and a reply that only the thread connects to it. Step 5's `ask_user` makes the same exchange one turn that waits for the person who asked.

### The rows, the case and your role, read directly

The chat service's log rows since step 3, acme's open cases, step 6's case and your role document, read without the chat service.

#### Do it: the log rows

The chat service's `chat` and `desk_gate` rows since step 3, from Cloud Logging. The cell names each account by the part of its email before the @.

There are two `desk_gate` rows: the Desk page's turn, as you, and step 6's, as `documind-evalacme-sa`. Each carries the class `human_requested`, the method `rule` and the rules version. A request for a person is not sensitive, so the row names the person; a POSH row would say `sensitive` and name nobody. The door answered both turns, so neither has a `chat` row. There are four `chat` rows, one for each turn the LangGraph brain ran: the near miss and the three clarifying turns, each with its model calls, tokens and cost. No row says that a turn waited, because none did.

#### Do it: the case and your role

`make cases` lists acme's open cases, soonest due first. Then the cell reads step 6's case and your role document from Firestore.

`make cases` lists the request you sent on the Desk page, acknowledged, in `people`, beside any of lesson 5.6's cases still open, which it shows as `sensitive`. Step 6's case is not in the list, because it is withdrawn. Its record keeps the words the cell sent, with source `button` and via `direct`, like any case raised from the button, and no audit event left pending. The token is kept only as its hash. Your role document holds the five roles, set by you.

### The approval wired in: a withdrawal paused on your lane, decided over REST, run by you

One company's switch, the LangGraph brain with the approve node, the pause as a record, the hold, who decides, and your run of the approved withdrawal. Then the switch back off.

#### Definition

Step 4's pause reaches your lane through one module, `services/chat/approval_routes.py`, and one call in `chat()`. The call gives back the brain it was given unless the company's `tenant_settings.agent_actions` is `approval` and the turn asked for the LangGraph brain. Then the brain is `build_approval_graph()` on the service's own checkpointer and model, and three things follow from the pause being data. The pause becomes a record, `approvals/{id}`, whose id is the thread and the checkpoint the pause is kept in, so the same pause read twice is one record. The conversation is held: a new question on a paused thread would drop the pause, so `POST /v1/chat` answers 409 until someone decides. And the decision is a route, `POST /v1/approvals/{id}/decide`, which checks the record before `decide()` runs: 404 unless the reader may read it, 410 once `expire_at` has passed (24 hours after the pause, checked in code), 409 once decided, 403 for the person who asked approving their own request, and for a second person who is not on this company's roster or does not hold `doc_approver`, which the route passes as `may_approve`. The approval withdraws nothing by itself. The tool's injected executor writes the approved withdrawal on the record, and you run it from your shell with `make withdraw-run`, which re-checks the record and writes the tombstone `make retire` writes, then marks the record withdrawn with one `doc.withdraw` event.

The records are `shared/approvals.py`'s, laid out like the case queue's, with the database client passed in. Its docstring lists what each function does; the record's statuses are `pending`, `approved`, `rejected`, `cancelled`, `answered`, `failed`, `expired`, `lost`, `withdrawn`.

The decision route, in full. `decide()` runs for the person who asked, with a Meter of its own, and the record then says what the decisions amounted to: `approved` when the tool ran, `rejected` or `cancelled` for a reject, `answered` for a question, `failed` when an approved tool refused. The resumed turn logs a `chat` row of the same shape as `chat()`'s, with surface `approval`.

The operator's half. `reconcile.py --approved` re-reads the record and checks it again, then runs `--retire`'s own branch through `main()`, so the tombstone is written by the one path lessons 1.7 and 7.4 show; the two `mirror` calls lesson 7.3 counts are still two. `make retire` from the shell writes no audit event; this run writes `doc.withdraw`.

Two lines elsewhere complete it: `doc_approver` joined `ROLES` in `shared/roles.py`, and the four actions joined `AUDIT_ACTIONS` in `shared/audit_log.py`, which lesson 4.8 counts.

#### Do it: the kit's own tests, offline

The whole flow runs on the kit's own chat service with a fake Firestore and a scripted model, at Rs 0: the switch off, then on; the pause and its record; the hold; the requester's own approval refused; another company's approver and a colleague without the role seeing nothing; the second person's approval; a rejection beside a search; a question only the asker answers; an expired record, and the hold ending its pause; a lost pause; and `--approved` on the record. 18 tests, in `~/graph-venv` from step 4.

#### Do it: switch acme on, and name the second person

`make agent-actions` writes `agent_actions` into acme's `tenant_settings`, beside the Desk's switches, and prints them; the chat service reads it within a minute. `make roles` gives `documind-evalacme-sa` the `doc_approver` role beside `employee`: the eval account stands in for a colleague who may approve, as it stood in for an acme employee in lesson 5.6. The requester will be `documind-ui-sa`, on acme's roster since lesson 5.1's smoke.

#### Do it: the flow, live

`make smoke-approval` runs the flow once against your chat service, printing each step. As `documind-ui-sa` it asks the LangGraph brain to withdraw `townhall_2026_q1.md`, a small acme document: the turn pauses, and the reply carries the record. The same session's next question is held. The requester's own approval is refused. `documind-evalzeta-sa`, on zeta's roster, cannot tell the record exists. The approver's list shows it. `documind-evalacme-sa` approves it, and the turn resumes: the tool runs, records the approved withdrawal, and the model answers that the operator will run it. A second decision is refused. Then a second withdrawal on a new session, which the approver rejects with a reason: the call errors alone and the model says nothing was withdrawn. The smoke withdraws nothing; it ends by printing your next two commands.

Every status came from the record's checks, not from the model: 200 with `pending` from the pause, 409 from the hold, 403 from four eyes, 404 from a reader who may not read, 200 with `approved` from the second person, 409 once decided, 200 with `rejected` from the reason. The two turns that paused cost one model call each, and each resume one more; the refusals cost nothing. The smoke depends on the model choosing `withdraw_document` for a question that names the file; if it answers in words instead, the smoke says so and stops, and nothing on your lane has changed.

#### Do it: run the approved withdrawal

The approval queued the work; you run it. The cell reads the approved record's id as the requester, runs `make withdraw-run` for it, and lists acme's sources, where the document's ledger row now says `withdrawn`.

`reconcile.py --approved` read the record, checked it again (approved, not yet run, by a second person who still holds `doc_approver` in acme, for an acme document), then ran `--retire`'s own branch: the `reconcile_withdrawn` line is `make retire`'s, with every retired chunk id, and the `reconcile_approved` line after it names the record, who asked, who approved and who ran it, and the way back. The record is `withdrawn`, and the bucket has its `doc.withdraw` event. Until this run, the document was still in search: the approval is a decision, the run is the deed.

#### Do it: the records and the events, read directly

Acme's approval records from Firestore, oldest first, and today's approval events in the audit bucket, read without the chat service.

Two records: the first `withdrawn`, with its withdrawal naming `documind-evalacme-sa` as the approver and you as the one who ran it; the second `rejected`. Neither carries a question or a reason beyond its results, and `audit_pending` is empty on both: every event reached the bucket. The bucket holds `approval.request` twice, `approval.approve` and `approval.reject` once each, and one `doc.withdraw`, each with the account that acted as its actor, as `role.grant` names the operator. A case event names a case reference instead (lesson 5.6): an approval is a decision about a document, and who made it is its point.

#### Do it: bring the document back, and switch acme off

`make restore` lifts the tombstone, as lesson 1.7 showed, and the worker returns the document. Then `make agent-actions` writes `off`, and acme's LangGraph brain is again the one lessons 5.4, 5.5 and 5.7 show, within a minute.

The restore's line is lesson 1.7's: the tombstone to `retired`, the object rewritten onto itself, the worker's `ingest_reactivated` inside the undo window. The switch's line prints acme's switches with `agent_actions` `off`. Your lane's chat service is what it was; the records and the events stay, as a decision's trail should.

### Why it is shaped this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments and tests, then the bill and the gaps.

- The pause is data. `interrupt()` leaves no request waiting in memory: the turn becomes a checkpoint, so any process that reads the same checkpointer can resume it, as step 5's second process did.

- The person who asked comes from the thread. `owner()` reads `tenant:user:session`, which the server builds from the verified caller. A model's arguments, a request body and the context a resume brings cannot name anyone else.

- Three locks, one rule. `decide()` refuses a person before anything runs. The approve node checks again, because a resume can reach the graph without `decide()`. The tool checks the approval of its own call, because it can be bound with no node in front of it, as the kit's test binds it. The panel in step 1 shows all three.

- Reject is not approve. The person who asked may cancel their own request. Only a second person may let it run.

- Nothing above interrupt() has a side effect. A resumed node runs again from its first line, as the Change-it showed.

- A rejected call errors alone. The refuse node refuses a whole turn (lesson 5.4). The approve node holds back only the call it was asked about: a search asked for beside a rejected withdrawal still runs, and the model is told the truth about each.

- Offer, never raise. `offer_case` and the chat door's `case_offer` offer a case. Only the person raises one, by pressing the button and confirming. Neither offer writes a record.

- Two forms, one record. The approve node serves a hand-built graph, and `HumanInTheLoopMiddleware` serves `create_agent`. `paused()` reads both the same way, so one route could serve either brain; the routes serve the graph.

- One switch, per company, off by default. `agent_actions` lives in `tenant_settings` beside the Desk's switches and is read the same way, once a minute. A company that never wrote it has the brain it had, and so does every other brain. The build checks that `approval_routes.py` is the one importer and that the call in `chat()` gives the brain back unchanged when the switch is off.

- The record is the truth, and it expires. The pause lives in the checkpointer, but what a route may do with it is read from the record: 404, 410, 409 and 403 are the record's answers, checked in code before `decide()` runs. A pause nobody decided within 24 hours is `expired`; the next question ends it as the asker's own cancel, a reject with the reason through `decide()` and the approve node, so the model is told and answers that turn, and then the question runs. Nothing writes the thread's state from outside the graph: `limits.repair_thread` stays the kit's one such writer (lesson 6.8).

- The approval is a decision; the run is the deed. The service never withdraws. The executor writes the approved withdrawal on the record, and the operator's `make withdraw-run` re-checks it and writes the tombstone, through `--retire`'s own branch. A record the operator never runs stays `approved` and withdraws nothing.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- One brain, behind the switch. Only the LangGraph brain pauses, and only for a company whose `agent_actions` is `approval`. The LangChain brain keeps lesson 5.4's guard, although `hitl_middleware()` is its form; the ADK brain has no form at all, and the direct brain has no loop. A company that never set the switch has no pause, no record and no route that does anything.

- The approval withdraws nothing. An approved record waits for the operator's `make withdraw-run`; there is no job that runs it, and nobody is told that a record waits except by `GET /v1/approvals`. A record that expires at 24 hours is marked so when it is next read or decided, by code: no TTL policy touches the collection, and nothing wakes a paused conversation on its own.

- The Chat page shows no waiting card. The pause reaches a person as the turn's answer and the `approval` field of the response; deciding is a REST call. The Chat page shows the answer and offers no button, and no inbox shows a `doc_approver` what waits.

- Clarification on your lane is words, until the switch is on. With it off, the brains hold `retrieve` and `calculate_processing_cost`, so a model that lacks a fact asks in its answer and the turn ends, and nothing records that it asked. With it on, `ask_user` pauses the turn as a record of kind `answer`, which the person who asked alone can read and answer.

- Escalation on your lane is by rule, until the switch is on. The gate reads words, not meaning (lesson 5.6). With the switch on, a model may offer a case where the rules missed, and the reply carries `case_offer` as the door's does; nothing is raised until the person presses the button.

- The ADK brain has no pause. `approval.py` pauses a LangGraph graph and LangChain's `create_agent`. It has no form for the ADK brain lesson 5.7 compares.

### Verify it yourself: the checklist

Twenty-two checks, each one block above, each with the value that proves it.

Your role document holds `people_ops` beside lesson 5.6's four roles, set by you, with one `role.grant` event in the audit bucket. acme has one more open case, the request you sent on the Desk page, acknowledged, in the People team's queue. Step 6's case is withdrawn. Both left case events in the audit bucket. The LangGraph brain keeps three new threads: `lesson108-esc` with the near miss, `lesson108` with two turns and `lesson108-new` with one. The chat service's log has this lesson's two `desk_gate` rows and four `chat` rows. Your home folder has `~/lesson108_case.txt` and `~/lesson108_threads.db`, and `~/graph-venv` has the SQLite checkpointer. `approval.py` is the kit's again: the Change-it put it back. Step 8 left `documind-evalacme-sa` holding `doc_approver`, two approval records under `approvals/` (one `withdrawn`, one `rejected`) with their five audit events, two more threads in the checkpointer, and `townhall_2026_q1.md` restored to acme's index; acme's `agent_actions` is `off` again, so nothing that answers a turn is changed and no turn pauses on your lane. Module 6 opens with what rides every model call, and lesson 6.8 resumes a paused or cut-off turn from its checkpoint.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.8 Pause, approve, clarify and escalate: human in the loop · v5.0

Next: Lesson 6.1 Assemble the context: what rides every model call.
